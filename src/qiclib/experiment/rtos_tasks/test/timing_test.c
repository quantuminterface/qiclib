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
#include "task.h"

#include "sequencer.h"
#include "recording.h"
#include "mem_io.h"

#define TEMP_MEM_SIZE 1024

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
void fix_fft(iq_pair *f, int32_t *ref)
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

int task_entry(void)
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t test_code = param_list[0];
    uint32_t iterations = param_list[1];

    uint32_t *data = (uint32_t *)rtos_GetDataBox(iterations * sizeof(uint32_t));

    // For some reasons the first calls of these functions sometimes take longer...
    // -> call them here twice in order to ensure that everything is deterministic afterwards
    // TODO: Why is this happening?
    rtos_EnterCriticalSection();
    rtos_RestartTimer();
    rtos_GetNsTimer();
    rtos_ExitCriticalSection();
    rtos_EnterCriticalSection();
    rtos_RestartTimer();
    rtos_GetNsTimer();
    rtos_ExitCriticalSection();

    uint32_t *temp_memory0 = (uint32_t *)rtos_GetDataBox(TEMP_MEM_SIZE * 4);
    uint32_t *temp_memory1 = (uint32_t *)rtos_GetDataBox(TEMP_MEM_SIZE * 4);
    uint32_t *temp_memory2 = (uint32_t *)rtos_GetDataBox(TEMP_MEM_SIZE * 4);
    int64_t *temp_memory3 = (int64_t *)rtos_GetDataBox(TEMP_MEM_SIZE * 4 * 2);
    int64_t *temp_memory4 = (int64_t *)rtos_GetDataBox(TEMP_MEM_SIZE * 4 * 2);
    iq_pair *temp_iq_pair0 = (iq_pair *)rtos_GetDataBox(TEMP_MEM_SIZE * 4 * 2);

    // Init for complex mult
    iq_pair_raw *D1 = (iq_pair_raw *)temp_memory0;
    iq_pair_raw *D2 = (iq_pair_raw *)temp_memory1;
    iq_pair *mult = (iq_pair *)temp_memory3;

    // Initialize reference as a sine wave (required for fft algorithm)
    int32_t *fft_ref = rtos_GetDataBox((N_WAVE - N_WAVE / 4) * sizeof(int32_t));
    int16_t *fft_ref_16 = rtos_GetDataBox((N_WAVE - N_WAVE / 4) * sizeof(int16_t));
    for (int samp = 0; samp < (N_WAVE - N_WAVE / 4); samp++)
    {
        fft_ref[samp] = (int32_t)(ref_amp * sin(2 * M_PI * (1 / ((double)N_WAVE)) * (double)(samp)));
        fft_ref_16[samp] = (int16_t)(ref_amp_16 * sin(2 * M_PI * (1 / ((double)N_WAVE)) * (double)(samp)));
    }

    for (uint32_t i = 0; i < iterations; i++)
    {
        rtos_EnterCriticalSection();
        switch (test_code)
        {
        // Do nothing (determine overhead by measurement)
        case 0:
            rtos_RestartTimer();

            //Do nothing

            data[i] = rtos_GetNsTimer();
            break;

        // Obtain the busy signal from sequencer
        case 1:
            rtos_RestartTimer();

            seq_is_busy();

            data[i] = rtos_GetNsTimer();
            break;

        // AXI4Lite Register read
        case 2:
            rtos_RestartTimer();

            ioread32(0xAA000000);

            data[i] = rtos_GetNsTimer();
            break;

        // AXI4Lite Register write
        case 3:
            rtos_RestartTimer();

            iowrite32(0xAA110040, 42);

            data[i] = rtos_GetNsTimer();
            break;

        // Memcopy 1024 registers into DRAM
        case 4:
            rtos_RestartTimer();

            memcpy(temp_memory0, (void *)0xAA202000, TEMP_MEM_SIZE * 4);

            data[i] = rtos_GetNsTimer();
            break;

        // Multiply 1024 32bit values in DRAM
        case 5:
            rtos_RestartTimer();

            for (int i = 0; i < TEMP_MEM_SIZE; i += 1)
            {
                temp_memory0[i] = temp_memory1[i] * temp_memory2[i];
            }

            data[i] = rtos_GetNsTimer();
            break;

        // Acquire data box
        case 6:
            rtos_RestartTimer();

            void *db = rtos_GetDataBox(TEMP_MEM_SIZE * sizeof(int64_t));

            data[i] = rtos_GetNsTimer();

            rtos_DiscardDataBox(db);
            break;

        // Initialize data box
        case 7:
            rtos_RestartTimer();

            for (int x = 0; x < TEMP_MEM_SIZE; x++)
            {
                temp_memory3[x] = 0;
            }

            data[i] = rtos_GetNsTimer();
            break;

        // Initialize two data boxes
        case 8:
            rtos_RestartTimer();

            for (int x = 0; x < TEMP_MEM_SIZE; x++)
            {
                temp_memory3[x] = 0;
                temp_memory0[x] = 0;
            }

            data[i] = rtos_GetNsTimer();
            break;

        // 16bit Complex product of two arrays
        case 9:
            rtos_RestartTimer();

            for (int samp = 0; samp < TEMP_MEM_SIZE; samp++)
            {
                mult[samp].i = ((int32_t)(D1[samp].i) * (int32_t)(D2[samp].i) +
                                (int32_t)(D1[samp].q) * (int32_t)(D2[samp].q));
                mult[samp].q = ((int32_t)(D1[samp].i) * (int32_t)(D2[samp].q) -
                                (int32_t)(D1[samp].q) * (int32_t)(D2[samp].i));
            }

            data[i] = rtos_GetNsTimer();
            break;

        // 32bit FFT
        case 10:
            rtos_RestartTimer();

            fix_fft(mult, fft_ref);

            data[i] = rtos_GetNsTimer();
            break;

        // 16bit FFT
        case 11:
            rtos_RestartTimer();

            fix_fft_16(D1, fft_ref_16);

            data[i] = rtos_GetNsTimer();
            break;

        // 32bit complex product of one array with its inverse
        case 12:
            rtos_RestartTimer();

            for (int samp = 0; samp < N_WAVE; samp++)
            {
                temp_memory3[samp] += ((int64_t)(temp_iq_pair0[(N_WAVE - samp) % N_WAVE].i) * (int64_t)(temp_iq_pair0[samp].i) -
                                       (int64_t)(temp_iq_pair0[(N_WAVE - samp) % N_WAVE].q) * (int64_t)(temp_iq_pair0[samp].q));
                temp_memory4[samp] += ((int64_t)(temp_iq_pair0[(N_WAVE - samp) % N_WAVE].i) * (int64_t)(temp_iq_pair0[samp].q) +
                                       (int64_t)(temp_iq_pair0[(N_WAVE - samp) % N_WAVE].q) * (int64_t)(temp_iq_pair0[samp].i));
            }

            data[i] = rtos_GetNsTimer();
            break;

        // Memset to initialize 64bit data box
        case 13:
            rtos_RestartTimer();

            memset(*temp_memory3, 0, TEMP_MEM_SIZE * sizeof(int64_t));

            data[i] = rtos_GetNsTimer();
            break;

        // Memset to initialize 32bit data box
        case 14:
            rtos_RestartTimer();

            memset(*temp_memory0, 0, TEMP_MEM_SIZE * sizeof(uint32_t));

            data[i] = rtos_GetNsTimer();
            break;

        // Default action stops task -> not intended to use
        default:
            rtos_PrintfError("Unknown test no. %d", test_code);
            return 1;
        }
        rtos_ExitCriticalSection();
        rtos_SetProgress(i + 1);
    }

    rtos_FinishDataBox(data);
    rtos_DiscardDataBox(temp_memory0);
    rtos_DiscardDataBox(temp_memory1);
    rtos_DiscardDataBox(temp_memory2);
    rtos_DiscardDataBox(temp_memory3);
    rtos_DiscardDataBox(temp_memory4);
    rtos_DiscardDataBox(temp_iq_pair0);
    return 0;
}
