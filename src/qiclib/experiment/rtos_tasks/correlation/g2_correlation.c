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

#define G2CALC_SAMPLE_NUM 1024

void g2calc_real_part(int64_t *dest, uint32_t samp_num, iq_pair_raw *D1, iq_pair_raw *D2, uint32_t tau, uint32_t shift)
{
    for (int t = 0; t < samp_num; t++)
    {
        *dest += ((int64_t)(D1[t].i) * (int64_t)(D1[(t + tau)].i) * (int64_t)(D2[(t + tau)].i) * (int64_t)(D2[t].i) - (int64_t)(D1[t].i) * (int64_t)(D1[(t + tau)].i) * (int64_t)(D2[(t + tau)].q) * (int64_t)(D2[t].q) + (int64_t)(D1[t].q) * (int64_t)(D1[(t + tau)].i) * (int64_t)(D2[(t + tau)].q) * (int64_t)(D2[t].i) + (int64_t)(D1[t].q) * (int64_t)(D1[(t + tau)].i) * (int64_t)(D2[(t + tau)].i) * (int64_t)(D2[t].q) + (int64_t)(D1[t].i) * (int64_t)(D1[(t + tau)].q) * (int64_t)(D2[(t + tau)].q) * (int64_t)(D2[t].i) + (int64_t)(D1[t].i) * (int64_t)(D1[(t + tau)].q) * (int64_t)(D2[(t + tau)].i) * (int64_t)(D2[t].q) - (int64_t)(D1[t].q) * (int64_t)(D1[(t + tau)].q) * (int64_t)(D2[(t + tau)].i) * (int64_t)(D2[t].i) + (int64_t)(D1[t].q) * (int64_t)(D1[(t + tau)].q) * (int64_t)(D2[(t + tau)].q) * (int64_t)(D2[t].q)) >> shift;
    }
}

void g2calc_imag_part(int64_t *dest, uint32_t samp_num, iq_pair_raw *D1, iq_pair_raw *D2, uint32_t tau, uint32_t shift)
{
    for (int t = 0; t < samp_num; t++)
    {
        *dest += ((int64_t)(D1[t].i) * (int64_t)(D1[(t + tau)].i) * (int64_t)(D2[(t + tau)].q) * (int64_t)(D2[t].i) + (int64_t)(D1[t].i) * (int64_t)(D1[(t + tau)].i) * (int64_t)(D2[(t + tau)].i) * (int64_t)(D2[t].q) - (int64_t)(D1[t].q) * (int64_t)(D1[(t + tau)].i) * (int64_t)(D2[(t + tau)].i) * (int64_t)(D2[t].i) + (int64_t)(D1[t].q) * (int64_t)(D1[(t + tau)].i) * (int64_t)(D2[(t + tau)].q) * (int64_t)(D2[t].q) - (int64_t)(D1[t].i) * (int64_t)(D1[(t + tau)].q) * (int64_t)(D2[(t + tau)].i) * (int64_t)(D2[t].i) + (int64_t)(D1[t].i) * (int64_t)(D1[(t + tau)].q) * (int64_t)(D2[(t + tau)].q) * (int64_t)(D2[t].q) - (int64_t)(D1[t].q) * (int64_t)(D1[(t + tau)].q) * (int64_t)(D2[(t + tau)].q) * (int64_t)(D2[t].i) - (int64_t)(D1[t].q) * (int64_t)(D1[(t + tau)].q) * (int64_t)(D2[(t + tau)].i) * (int64_t)(D2[t].q)) >> shift;
    }
}

int task_entry()
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
    if (param_count != 7)
    {
        rtos_ReportError("Please provide exactly 7 parameter values for the task.");
        return -1;
    }
    uint32_t averages = param_list[0];
    uint32_t iterations = param_list[1];
    uint32_t tau_max = param_list[2]; // here tau_max is in t_samp
    uint32_t pc_start = param_list[3];
    uint32_t pc_start_ss = param_list[4];
    uint32_t measure_ss = param_list[5]; // 0 if no background, >0 otherwise
    uint32_t shift_result = param_list[6];

    uint32_t samp_num = G2CALC_SAMPLE_NUM - tau_max;

    // Temporary data storage to collect the result values from the recording modules
    struct iq_pair_raw *iq_pair_D1 = rtos_GetDataBox(G2CALC_SAMPLE_NUM * sizeof(iq_pair_raw));
    struct iq_pair_raw *iq_pair_D2 = rtos_GetDataBox(G2CALC_SAMPLE_NUM * sizeof(iq_pair_raw));

    // Pointer for the result databoxes
    int64_t *g2_result_real, *g2_result_imag, *g2_result_ss_real, *g2_result_ss_imag;

    for (int its = 0; its < iterations; its++)
    {
        // Databoxes for the results
        g2_result_real = rtos_GetDataBox(tau_max * sizeof(int64_t));
        g2_result_imag = rtos_GetDataBox(tau_max * sizeof(int64_t));
        // Initialize the memory with zeros (needed for summing & averaging)
        for (int i = 0; i < tau_max; i++)
        {
            g2_result_real[i] = 0;
            g2_result_imag[i] = 0;
        }

        if (measure_ss)
        {
            // Same for the background
            g2_result_ss_real = rtos_GetDataBox(tau_max * sizeof(int64_t));
            g2_result_ss_imag = rtos_GetDataBox(tau_max * sizeof(int64_t));
            for (int i = 0; i < tau_max; i++)
            {
                g2_result_ss_real[i] = 0;
                g2_result_ss_imag[i] = 0;
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

            rec_get_result_memory(0, iq_pair_D1, G2CALC_SAMPLE_NUM);
            rec_get_result_memory(1, iq_pair_D2, G2CALC_SAMPLE_NUM);

            for (uint32_t tau = 0; tau < tau_max; tau++)
            {
                g2calc_real_part(g2_result_real + tau, samp_num, iq_pair_D1, iq_pair_D2, tau, shift_result);
                g2calc_imag_part(g2_result_imag + tau, samp_num, iq_pair_D1, iq_pair_D2, tau, shift_result);
            }

            // Skip background measurement if not to measure
            if (!measure_ss)
                continue;

            seq_start_at(pc_start_ss);

            seq_wait_while_busy();
            rec_wait_while_busy(0);
            rec_wait_while_busy(1);

            rec_get_result_memory(0, iq_pair_D1, samp_num);
            rec_get_result_memory(1, iq_pair_D2, samp_num);

            for (uint32_t tau = 0; tau < tau_max; tau++)
            {
                g2calc_real_part(g2_result_ss_real + tau, samp_num, iq_pair_D1, iq_pair_D2, tau, shift_result);
                g2calc_imag_part(g2_result_ss_imag + tau, samp_num, iq_pair_D1, iq_pair_D2, tau, shift_result);
            }
        }

        rtos_SetProgress((its + 1) * averages);

        // Do not allow any disturbance while finishing the databoxes -> always add all at once
        rtos_EnterCriticalSection();
        rtos_FinishDataBox(g2_result_real);
        rtos_FinishDataBox(g2_result_imag);
        if (measure_ss)
        {
            rtos_FinishDataBox(g2_result_ss_real);
            rtos_FinishDataBox(g2_result_ss_imag);
        }
        rtos_ExitCriticalSection();
    }

    // Discard temporary databoxes
    rtos_DiscardDataBox(iq_pair_D1);
    rtos_DiscardDataBox(iq_pair_D2);

    return 0;
}
