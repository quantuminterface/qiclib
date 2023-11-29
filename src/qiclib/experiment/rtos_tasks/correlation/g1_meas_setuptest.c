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

#define G1CALC_SAMPLE_NUM 1024

int task_entry(void)
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();

    //uint32_t tau_max = param_list[0];  // here tau_max is in t_samp
    uint32_t averages = param_list[1];
    uint32_t pc_start = param_list[2];
    uint32_t pc_start_ss = param_list[3];
    //uint32_t shift_result = param_list[4];

    // These will now collect the averages of result memory
    int32_t *d1_i = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(int32_t));
    int32_t *d1_q = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(int32_t));
    int32_t *d2_i = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(int32_t));
    int32_t *d2_q = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(int32_t));
    int32_t *d1_i_ss = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(int32_t));
    int32_t *d1_q_ss = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(int32_t));
    int32_t *d2_i_ss = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(int32_t));
    int32_t *d2_q_ss = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(int32_t));

    for (int i = 0; i < G1CALC_SAMPLE_NUM; i++)
    {
        d1_i[i] = 0;
        d1_q[i] = 0;
        d2_i[i] = 0;
        d2_q[i] = 0;
        d1_i_ss[i] = 0;
        d1_q_ss[i] = 0;
        d2_i_ss[i] = 0;
        d2_q_ss[i] = 0;
    }

    struct iq_pair_raw *iq_pair_g1_D1 = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(iq_pair_raw));
    struct iq_pair_raw *iq_pair_g1_D2 = rtos_GetDataBox(G1CALC_SAMPLE_NUM * sizeof(iq_pair_raw));

    seq_wait_while_busy(); //Wait for previous task to finish

    for (int i = 0; i < averages; i++)
    {

        // Reset data of both recording modules before starting
        // rec_trigger_manually(0, 14);
        // rec_trigger_manually(1, 14); // not automatically done here
        seq_start_at(pc_start);

        seq_wait_while_busy();
        rec_wait_while_busy(0);
        rec_wait_while_busy(1);
        // We only wait until we have enough data
        //while (!(
        //    rec_is_result_memory_full(0) &&
        //    rec_is_result_memory_full(1))) {}

        rec_get_result_memory(0, iq_pair_g1_D1, G1CALC_SAMPLE_NUM);
        rec_get_result_memory(1, iq_pair_g1_D2, G1CALC_SAMPLE_NUM);

        for (uint32_t i = 0; i < G1CALC_SAMPLE_NUM; i++)
        {
            *(d1_i + i) += iq_pair_g1_D1[i].i;
            *(d1_q + i) += iq_pair_g1_D1[i].q;
            *(d2_i + i) += iq_pair_g1_D2[i].i;
            *(d2_q + i) += iq_pair_g1_D2[i].q;
        }
        /* for (uint32_t tau=0; tau <= tau_max; tau++)
        {
            g1calc_real_part(g1_result_real + tau, samp_num, iq_pair_g1_D1, iq_pair_g1_D2, tau, shift_result);
            g1calc_imag_part(g1_result_imag + tau, samp_num, iq_pair_g1_D1, iq_pair_g1_D2, tau, shift_result);
        } */

        // Reset data of both recording modules before starting
        // rec_trigger_manually(0, 14);
        // rec_trigger_manually(1, 14); // not automatically done here
        seq_start_at(pc_start_ss);

        seq_wait_while_busy();
        rec_wait_while_busy(0);
        rec_wait_while_busy(1);
        // We only wait until we have enough data
        //while (!(
        //    rec_is_result_memory_full(0) &&
        //    rec_is_result_memory_full(1))) {}

        rec_get_result_memory(0, iq_pair_g1_D1, G1CALC_SAMPLE_NUM);
        rec_get_result_memory(1, iq_pair_g1_D2, G1CALC_SAMPLE_NUM);

        for (uint32_t i = 0; i < G1CALC_SAMPLE_NUM; i++)
        {
            *(d1_i_ss + i) += iq_pair_g1_D1[i].i;
            *(d1_q_ss + i) += iq_pair_g1_D1[i].q;
            *(d2_i_ss + i) += iq_pair_g1_D2[i].i;
            *(d2_q_ss + i) += iq_pair_g1_D2[i].q;
        }
        /* for (uint32_t tau=0; tau <= tau_max; tau++)
        {
            g1calc_real_part(g1_result_ss_real + tau, samp_num, iq_pair_g1_D1, iq_pair_g1_D2, tau, shift_result);
            g1calc_imag_part(g1_result_ss_imag + tau, samp_num, iq_pair_g1_D1, iq_pair_g1_D2, tau, shift_result);
        } */
        rtos_SetProgress(i);
    }

    rtos_FinishDataBox(d1_i);
    rtos_FinishDataBox(d1_q);
    rtos_FinishDataBox(d2_i);
    rtos_FinishDataBox(d2_q);

    rtos_FinishDataBox(d1_i_ss);
    rtos_FinishDataBox(d1_q_ss);
    rtos_FinishDataBox(d2_i_ss);
    rtos_FinishDataBox(d2_q_ss);

    return 42;
}
