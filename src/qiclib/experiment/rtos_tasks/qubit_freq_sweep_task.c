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
#include <string.h>

#include "task.h"
#include "recording.h"
#include "sequencer.h"
#include "pulsegen.h"

int task_entry(void)
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t averages = (param_list++)[0];
    uint32_t freq_min = (param_list++)[0];
    uint32_t freq_max = (param_list++)[0];
    uint32_t freq_step = (param_list++)[0];
    uint32_t freq_nop = (freq_max - freq_min) / freq_step;
    uint32_t *pc_dict = param_list;

    uint32_t freqs[freq_nop];
    uint32_t freq_point, i;

    for (freq_point = 0; freq_point < freq_nop; freq_point++)
    {
        freqs[freq_point] = freq_min + freq_step * freq_point;
    }

    /*locate place for result data*/
    int32_t *sum_dataI = rtos_GetDataBox(freq_nop * sizeof(int32_t));
    int32_t *sum_dataQ = rtos_GetDataBox(freq_nop * sizeof(int32_t));
    for (i = 0; i < freq_nop; i++)
    {
        sum_dataI[i] = 0;
        sum_dataQ[i] = 0;
    }
    /*locate place for IQ amplitudes from Recording*/
    iq_pair *data_iq = (iq_pair *)rtos_GetDataBox(sizeof(iq_pair));

    /* turn on manipulation pulse*/
    seq_start_at(pc_dict[0]);
    seq_wait_while_busy();
    for (i = 0; i < averages; i++)
    {
        /*the first sequence is finished here*/
        for (freq_point = 0; freq_point < freq_nop; freq_point++)
        {
            /*the manipulation pulse is supposed to be still holded, so here we only change it's frequecny and readout the result*/
            pg_set_internal_frequency_reg(freqs[freq_point]);
            seq_start_at(pc_dict[1]);
            seq_wait_while_busy();
            rec_wait_while_busy(0);
            /*get IQ amplitudes*/
            rec_get_averaged_result(0, data_iq);
            /*Sum data for each delay point to average*/

            sum_dataI[freq_point] += (int32_t)(data_iq->i);
            sum_dataQ[freq_point] += (int32_t)(data_iq->q);
        }
        rtos_SetProgress(i);
    }
    /*turns off manipulation signal*/
    seq_start_at(pc_dict[2]);
    seq_wait_while_busy();

    rtos_FinishDataBox(sum_dataI);
    rtos_FinishDataBox(sum_dataQ);

    return 42;
}
