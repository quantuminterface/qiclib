/* Copyright© 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
 * Richard Gebauer, IPE, Karlsruhe Institute of Technology
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
// Task to calculate g2 correlation function
#include "task.h"
#include "cells.h"

#include <math.h>
#define N_WAVE 1024    /* full length  */
#define LOG2_N_WAVE 10 /* log2(N_WAVE) */

#define ref_amp 0x7fffffff
#define ref_amp_16 0x7fff

typedef struct mult
{
    int32_t i;
    int32_t q;
} mult;

/*
    FIX_MPY() - fixed-point multiplication & scaling.
    Substitute inline assembly for hardware-specific
    optimization suited to a particluar DSP processor.
    Scaling ensures that result remains 32-bit.
*/
int32_t FIX_MPY(int32_t a, int32_t b)
{
    /* shift right one less bit (i.e. 15-1) */
    int64_t c = ((int64_t)a * (int64_t)b) >> 30;
    /* last bit shifted out = rounding-bit */
    b = c & 0x01;
    /* last shift + rounding bit */
    a = (c >> 1) + b;
    return a;
}
int16_t FIX_MPY_16(int16_t a, int16_t b)
{
    /* shift right one less bit (i.e. 15-1) */
    int32_t c = ((int32_t)a * (int32_t)b) >> 14;
    /* last bit shifted out = rounding-bit */
    b = c & 0x01;
    /* last shift + rounding bit */
    a = (c >> 1) + b;
    return a;
}
/*
    fix_fft() - perform forward fast Fourier transform.
    fr[n],fi[n] are real and imaginary arrays, both INPUT AND
    RESULT (in-place FFT), with 0 <= n < 2**m;
*/
void fix_fft(mult *f, int32_t *ref)
{
    int32_t mr, nn, z, j, l, k, zstep, n, qr, qi, tr, ti, wr, wi, m;

    m = LOG2_N_WAVE;
    n = 1 << m;
    mr = 0;
    nn = n - 1;

    /* decimation in time - re-order data */
    for (m = 1; m <= nn; ++m)
    {
        l = n;
        do
        {
            l >>= 1;
        } while (mr + l > nn);
        mr = (mr & (l - 1)) + l;

        if (mr <= m)
            continue;
        tr = f[m].i;
        f[m].i = f[mr].i;
        f[mr].i = tr;

        ti = f[m].q;
        f[m].q = f[mr].q;
        f[mr].q = ti;
    }

    l = 1;
    k = LOG2_N_WAVE - 1;
    while (l < n)
    {
        zstep = l << 1;
        for (m = 0; m < l; ++m)
        {
            j = m << k;
            /* 0 <= j < N_WAVE/2 */
            wr = (ref[j + N_WAVE / 4]) >> 1;
            wi = (-ref[j]) >> 1;

            for (z = m; z < n; z += zstep)
            {
                j = z + l;
                tr = FIX_MPY(wr, f[j].i) - FIX_MPY(wi, f[j].q);
                ti = FIX_MPY(wr, f[j].q) + FIX_MPY(wi, f[j].i);
                qr = f[z].i;
                qi = f[z].q;

                qr >>= 1;
                qi >>= 1;

                f[j].i = qr - tr;
                f[j].q = qi - ti;
                f[z].i = qr + tr;
                f[z].q = qi + ti;
            }
        }
        --k;
        l = zstep;
    }
}
void fix_fft_16(iq_pair_raw *f, int16_t *ref)
{
    int16_t mr, nn, z, j, l, k, zstep, n, qr, qi, tr, ti, wr, wi, m;

    m = LOG2_N_WAVE;
    n = 1 << m;
    mr = 0;
    nn = n - 1;

    /* decimation in time - re-order data */
    for (m = 1; m <= nn; ++m)
    {
        l = n;
        do
        {
            l >>= 1;
        } while (mr + l > nn);
        mr = (mr & (l - 1)) + l;

        if (mr <= m)
            continue;
        tr = f[m].i;
        f[m].i = f[mr].i;
        f[mr].i = tr;

        ti = f[m].q;
        f[m].q = f[mr].q;
        f[mr].q = ti;
    }

    l = 1;
    k = LOG2_N_WAVE - 1;
    while (l < n)
    {
        zstep = l << 1;
        for (m = 0; m < l; ++m)
        {
            j = m << k;
            /* 0 <= j < N_WAVE/2 */
            wr = (ref[j + N_WAVE / 4]) >> 1;
            wi = (-ref[j]) >> 1;

            for (z = m; z < n; z += zstep)
            {
                j = z + l;
                tr = FIX_MPY_16(wr, f[j].i) - FIX_MPY_16(wi, f[j].q);
                ti = FIX_MPY_16(wr, f[j].q) + FIX_MPY_16(wi, f[j].i);
                qr = f[z].i;
                qi = f[z].q;

                qr >>= 1;
                qi >>= 1;

                f[j].i = qr - tr;
                f[j].q = qi - ti;
                f[z].i = qr + tr;
                f[z].q = qi + ti;
            }
        }
        --k;
        l = zstep;
    }
}

void calc_g2(int64_t *dest_real, int64_t *dest_imag, iq_pair_raw *D1, iq_pair_raw *D2, int32_t *ref, mult *signal_mult)
{
    //Calulate the complex product of required signals
    for (int samp = 0; samp < N_WAVE; samp++)
    {
        signal_mult[samp].i = ((int32_t)(D1[samp].i) * (int32_t)(D2[samp].i) +
                               (int32_t)(D1[samp].q) * (int32_t)(D2[samp].q));
        signal_mult[samp].q = ((int32_t)(D1[samp].i) * (int32_t)(D2[samp].q) -
                               (int32_t)(D1[samp].q) * (int32_t)(D2[samp].i));
    }

    // Perform FFT for the result of multiplication
    fix_fft(signal_mult, ref);

    //Calculate the value of g2 function
    for (int samp = 0; samp < N_WAVE; samp++)
    {
        dest_real[samp] += ((int64_t)(signal_mult[(N_WAVE - samp) % N_WAVE].i) * (int64_t)(signal_mult[samp].i) -
                            (int64_t)(signal_mult[(N_WAVE - samp) % N_WAVE].q) * (int64_t)(signal_mult[samp].q));
        dest_imag[samp] += ((int64_t)(signal_mult[(N_WAVE - samp) % N_WAVE].i) * (int64_t)(signal_mult[samp].q) +
                            (int64_t)(signal_mult[(N_WAVE - samp) % N_WAVE].q) * (int64_t)(signal_mult[samp].i));
    }
}
void calc_g1(int64_t *dest_real, int64_t *dest_imag, iq_pair_raw *D1, iq_pair_raw *D2, int16_t *ref)
{
    fix_fft_16(D1, ref);
    fix_fft_16(D2, ref);

    for (int o = 0; o < N_WAVE; o++)
    {
        //The Real part of g-function is calculated
        dest_real[o] += ((int64_t)(D1[o].i) * (int64_t)(D2[o].i) + (int64_t)(D1[o].q) * (int64_t)(D2[o].q));
        //The Imag part of g-function is calculated
        dest_imag[o] += ((int64_t)(D1[o].i) * (int64_t)(D2[o].q) - (int64_t)(D1[o].q) * (int64_t)(D2[o].i));
    }
}

int task_entry()
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
    if (param_count != 9)
    {
        rtos_PrintfError("Please provide exactly 9 parameter values for the task (%d given).", param_count);
        return -1;
    }
    uint32_t averages = param_list[0];
    uint32_t iterations = param_list[1];
    uint32_t pc_start = param_list[2];
    uint32_t pc_start_ss = param_list[3];
    uint32_t cal_pc = param_list[4];
    uint32_t cal_averages = param_list[5];
    uint32_t cal_valueshift = param_list[6];
    uint32_t cal_recduration = param_list[7];
    uint32_t cal_mod_selection = param_list[8];

    // TODO Adapt everything to run with 2 unit cells
    // Also do not use data boxes for temporary data but just create an array in C (located in faster memory)
    rtos_PrintfError("This experiment needs to be adapted for new unit cell design first!");
    return 1;

    // Use the first and second cell
    uint8_t cell_count = cells_get_count();
    if (cell_count < 2)
    {
        rtos_PrintfError("For the correlation measurements, atleast two cells are needed!");
        return 1;
    }
    Cell *cell = cells_create();

    // Initialize reference as a sine wave (required for fft algorithm)
    int32_t *fft_ref = rtos_GetDataBox((N_WAVE - N_WAVE / 4) * sizeof(int32_t));
    int16_t *fft_ref_16 = rtos_GetDataBox((N_WAVE - N_WAVE / 4) * sizeof(int16_t));
    for (int samp = 0; samp < (N_WAVE - N_WAVE / 4); samp++)
    {
        fft_ref[samp] = (int32_t)(ref_amp * sin(2 * M_PI * (1 / ((double)N_WAVE)) * (double)(samp)));
        fft_ref_16[samp] = (int16_t)(ref_amp_16 * sin(2 * M_PI * (1 / ((double)N_WAVE)) * (double)(samp)));
    }

    // Temporary data storage to collect the result values from the recording modules
    struct iq_pair_raw *iq_pair_D1 = rtos_GetDataBox(N_WAVE * sizeof(iq_pair_raw));
    struct iq_pair_raw *iq_pair_D2 = rtos_GetDataBox(N_WAVE * sizeof(iq_pair_raw));
    struct mult *signal_mult = rtos_GetDataBox(N_WAVE * sizeof(mult));
    iq_pair *cal_meas_D1 = rtos_GetDataBox(sizeof(iq_pair));
    iq_pair *cal_meas_D2 = rtos_GetDataBox(sizeof(iq_pair));

    // Pointer for the result databoxes
    int64_t *g1_result_real, *g1_result_imag, *g1_result_ss_real, *g1_result_ss_imag;
    int64_t *g2_result_real, *g2_result_imag, *g2_result_ss_real, *g2_result_ss_imag;

    for (int its = 0; its < iterations; its++)
    {
        if (its % cal_mod_selection == 0)
        {
            // Store current parameter temporarily - assume both recording modules are configured identically
            uint32_t old_valueshift = rec_get_value_shift(cell[0].recording);
            uint32_t old_recduration = rec_get_recording_duration(cell[0].recording);
            uint32_t old_averages = seq_get_averages(cell[0].sequencer);

            // Extract old phase offset
            uint16_t old_phaseoffset0 = rec_get_phase_offset_reg(cell[0].recording);
            uint16_t old_phaseoffset1 = rec_get_phase_offset_reg(cell[1].recording);

            // Set new values
            rec_set_value_shift(cell[0].recording, cal_valueshift);
            rec_set_value_shift(cell[1].recording, cal_valueshift);
            rec_set_recording_duration(cell[0].recording, cal_recduration);
            rec_set_recording_duration(cell[1].recording, cal_recduration);
            seq_set_averages(cell[0].sequencer, cal_averages);

            // Start calibration measurement
            seq_wait_while_busy(cell[0].sequencer);
            seq_start_at(cell[0].sequencer, cal_pc);

            // Wait until measurement finishes
            seq_wait_while_busy(cell[0].sequencer);
            rec_wait_while_busy(cell[0].recording);
            rec_wait_while_busy(cell[1].recording);

            // Fetch results from both Recording modules
            rec_get_averaged_result(cell[0].recording, cal_meas_D1);
            rec_get_averaged_result(cell[1].recording, cal_meas_D2);

            // ASSUME: D1 is near 0°, D2 near 180° -> correct small changes
            // phi(D1) = Q(D1) / I(D1)
            // phi(D2) = -Q(D2) / -I(D2)

            // Calculate new phase offsets
            // 2pi wrap happens implicitely by the uint16_t overflowing
            uint16_t new_phaseoffset0 = old_phaseoffset0 - rec_calc_phase_offset_reg(1. * cal_meas_D1->q / cal_meas_D1->i);
            uint16_t new_phaseoffset1 = old_phaseoffset1 - rec_calc_phase_offset_reg(1. * cal_meas_D2->q / cal_meas_D2->i);

            // Set new phase offsets
            rec_set_phase_offset_reg(cell[0].recording, new_phaseoffset0);
            rec_set_phase_offset_reg(cell[1].recording, new_phaseoffset1);

            // Restore old parameters
            rec_set_value_shift(cell[0].recording, old_valueshift);
            rec_set_value_shift(cell[1].recording, old_valueshift);
            rec_set_recording_duration(cell[0].recording, old_recduration);
            rec_set_recording_duration(cell[1].recording, old_recduration);
            seq_set_averages(cell[0].sequencer, old_averages);
        }

        // Databoxes for the results
        g1_result_real = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        g1_result_imag = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        g2_result_real = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        g2_result_imag = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        g1_result_ss_real = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        g1_result_ss_imag = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        g2_result_ss_real = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        g2_result_ss_imag = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        // Initialize the memory with zeros (needed for summing & averaging)
        for (int i = 0; i < N_WAVE; i++)
        {
            g1_result_real[i] = 0;
            g1_result_imag[i] = 0;
            g2_result_real[i] = 0;
            g2_result_imag[i] = 0;
            g1_result_ss_real[i] = 0;
            g1_result_ss_imag[i] = 0;
            g2_result_ss_real[i] = 0;
            g2_result_ss_imag[i] = 0;
        }

        seq_wait_while_busy(cell[0].sequencer); //Wait for previous tasks to finish

        // Inner loop with averages performed without reporting data
        for (int avg = 0; avg < averages; avg++)
        {
            rtos_SetProgress(avg + its * averages);

            seq_start_at(cell[0].sequencer, pc_start);

            seq_wait_while_busy(cell[0].sequencer);
            rec_wait_while_busy(cell[0].recording);
            rec_wait_while_busy(cell[1].recording);

            rec_get_result_memory(cell[0].recording, iq_pair_D1, N_WAVE);
            rec_get_result_memory(cell[1].recording, iq_pair_D2, N_WAVE);

            calc_g2(g2_result_real, g2_result_imag, iq_pair_D1, iq_pair_D2, fft_ref, signal_mult);
            // G1 is partly inplace so we perform it after G2
            calc_g1(g1_result_real, g1_result_imag, iq_pair_D1, iq_pair_D2, fft_ref_16);

            // Background measurement
            seq_wait_while_busy(cell[0].sequencer);
            seq_start_at(cell[0].sequencer, pc_start_ss);

            seq_wait_while_busy(cell[0].sequencer);
            rec_wait_while_busy(cell[0].recording);
            rec_wait_while_busy(cell[1].recording);

            rec_get_result_memory(cell[0].recording, iq_pair_D1, N_WAVE);
            rec_get_result_memory(cell[1].recording, iq_pair_D2, N_WAVE);

            calc_g2(g2_result_ss_real, g2_result_ss_imag, iq_pair_D1, iq_pair_D2, fft_ref, signal_mult);
            calc_g1(g1_result_ss_real, g1_result_ss_imag, iq_pair_D1, iq_pair_D2, fft_ref_16);
        }

        rtos_SetProgress((its + 1) * averages);

        // Do not allow any disturbance while finishing the databoxes -> always add all at once
        rtos_EnterCriticalSection();
        rtos_FinishDataBox(g1_result_real);
        rtos_FinishDataBox(g1_result_imag);
        rtos_FinishDataBox(g2_result_real);
        rtos_FinishDataBox(g2_result_imag);
        rtos_FinishDataBox(g1_result_ss_real);
        rtos_FinishDataBox(g1_result_ss_imag);
        rtos_FinishDataBox(g2_result_ss_real);
        rtos_FinishDataBox(g2_result_ss_imag);
        rtos_ExitCriticalSection();
    }

    // Discard temporary databoxes
    rtos_DiscardDataBox(iq_pair_D1);
    rtos_DiscardDataBox(iq_pair_D2);
    rtos_DiscardDataBox(signal_mult);

    return 0;
}
