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
#include "sequencer.h"
#include "recording.h"

#include <math.h>
#include <string.h>

#define N_WAVE 1024
#define LOG2_N_WAVE 10
#define ref_amp 0x7fff

/*
    FIX_MPY() - fixed-point multiplication & scaling.
    Substitute inline assembly for hardware-specific
    optimization suited to a particluar DSP processor.
    Scaling ensures that result remains 16-bit.
*/
int16_t FIX_MPY(int16_t a, int16_t b)
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
    fix_fft() - perform forward/inverse fast Fourier transform.
    fr[n],fi[n] are real and imaginary arrays, both INPUT AND
    RESULT (in-place FFT), with 0 <= n < 2**m;
*/

void fix_fft(iq_pair_raw *f, int16_t *ref)
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

void calc_g1(int64_t *dest_real, int64_t *dest_imag, iq_pair_raw *D1, iq_pair_raw *D2, int16_t *ref)
{
    fix_fft(D1, ref);
    fix_fft(D2, ref);

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
    if (param_count != 5)
    {
        rtos_PrintfError("Please provide exactly 5 parameter values for the task (%d given).", param_count);
        return -1;
    }
    uint32_t averages = param_list[0];
    uint32_t iterations = param_list[1];
    uint32_t pc_start = param_list[2];
    uint32_t pc_start_ss = param_list[3];
    uint32_t measure_ss = param_list[4]; // 0 if no background, >0 otherwise

    // Initialize reference as a sine wave (required for fft algorithm)
    int16_t *fft_ref = rtos_GetDataBox(N_WAVE * sizeof(int16_t));
    for (int samp = 0; samp < (N_WAVE - N_WAVE / 4); samp++)
    {
        fft_ref[samp] = (int16_t)(ref_amp * sin(2 * M_PI * (1 / ((double)N_WAVE)) * (double)(samp)));
    }

    // Temporary data storage to collect the result values from the recording modules
    struct iq_pair_raw *iq_pair_D1 = rtos_GetDataBox(N_WAVE * sizeof(iq_pair_raw));
    struct iq_pair_raw *iq_pair_D2 = rtos_GetDataBox(N_WAVE * sizeof(iq_pair_raw));

    // Pointer for the result databoxes
    int64_t *g1_result_real, *g1_result_imag, *g1_result_ss_real, *g1_result_ss_imag;

    for (int its = 0; its < iterations; its++)
    {
        // Databoxes for the results
        g1_result_real = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        g1_result_imag = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
        // Initialize the memory with zeros (needed for summing & averaging)
        for (int i = 0; i < N_WAVE; i++)
        {
            g1_result_real[i] = 0;
            g1_result_imag[i] = 0;
        }

        if (measure_ss)
        {
            // Same for the background
            g1_result_ss_real = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
            g1_result_ss_imag = rtos_GetDataBox(N_WAVE * sizeof(int64_t));
            for (int i = 0; i < N_WAVE; i++)
            {
                g1_result_ss_real[i] = 0;
                g1_result_ss_imag[i] = 0;
            }
        }

        seq_wait_while_busy(); //Wait for previous task to finish

        // Inner loop with averages performed without reporting data
        for (int avg = 0; avg < averages; avg++)
        {
            rtos_SetProgress(avg + its * averages);

            seq_start_at(pc_start);

            seq_wait_while_busy();
            rec_wait_while_busy(0);
            rec_wait_while_busy(1);

            rec_get_result_memory(0, iq_pair_D1, N_WAVE);
            rec_get_result_memory(1, iq_pair_D2, N_WAVE);

            calc_g1(g1_result_real, g1_result_imag, iq_pair_D1, iq_pair_D2, fft_ref);

            // Skip background measurement if not to measure
            if (!measure_ss)
                continue;

            seq_start_at(pc_start_ss);

            seq_wait_while_busy();
            rec_wait_while_busy(0);
            rec_wait_while_busy(1);

            rec_get_result_memory(0, iq_pair_D1, N_WAVE);
            rec_get_result_memory(1, iq_pair_D2, N_WAVE);

            calc_g1(g1_result_ss_real, g1_result_ss_imag, iq_pair_D1, iq_pair_D2, fft_ref);
        }

        rtos_SetProgress((its + 1) * averages);

        // Do not allow any disturbance while finishing the databoxes -> always add all at once
        rtos_EnterCriticalSection();
        rtos_FinishDataBox(g1_result_real);
        rtos_FinishDataBox(g1_result_imag);
        if (measure_ss)
        {
            rtos_FinishDataBox(g1_result_ss_real);
            rtos_FinishDataBox(g1_result_ss_imag);
        }
        rtos_ExitCriticalSection();
    }

    // Discard temporary databoxes
    rtos_DiscardDataBox(iq_pair_D1);
    rtos_DiscardDataBox(iq_pair_D2);

    return 0;
}
