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
#include "cells.h"

int task_entry(void)
{
    uint32_t i, j, k;

    uint32_t *param_list = (uint32_t *)rtos_GetParameters();

    uint32_t averages = (param_list++)[0];
    uint32_t nop = (param_list++)[0];
    uint32_t delays_num = (param_list++)[0];
    uint8_t cell_idx = (param_list++)[0];

    uint32_t *sequencer_pc = param_list;
    param_list += nop;

    /*set delays value*/
    uint32_t *delays[nop];
    for (i = 0; i < nop; i++)
    {
        delays[i] = param_list;
        param_list += delays_num;
    }

    // Check if the parameters are valid
    uint8_t cell_count = cells_get_count();
    if (cell_idx >= cell_count)
    {
        rtos_PrintfError(
            "Requested cell %d, but only 0 to %d available.",
            cell_idx,
            cell_count - 1);
        return 1;
    }

    // Fetch cell pointers from platform (do not forget to free at the end!)
    Cell *cells = cells_create();
    // Select relevant cell
    Cell cell = cells[cell_idx];

    /*locate a memory space for results averaging for each point of each delay registers*/
    int32_t *sum_dataI = rtos_GetDataBox(nop * sizeof(int32_t));
    int32_t *sum_dataQ = rtos_GetDataBox(nop * sizeof(int32_t));
    for (j = 0; j < nop; j++)
    {
        sum_dataI[j] = 0;
        sum_dataQ[j] = 0;
    }
    /*locate mem to IQ points for data averaging*/
    iq_pair *data_iq = rtos_GetDataBox(sizeof(iq_pair));

    cells_wait_while_busy(); //wait for previous task to finish

    for (i = 0; i < averages; i++)
    {
        for (j = 0; j < nop; j++)
        {
            /*set delay registers values*/
            for (k = 0; k < delays_num; k++)
            {
                seq_set_register(cell.sequencer, k + 1, delays[j][k]);
            }
            /*for each delay start the sequence*/
            seq_start_at(cell.sequencer, sequencer_pc[j]);
            cells_wait_while_cell_busy(cell_idx);
            /*get data from Recording module */
            rec_get_averaged_result(cell.recording, data_iq);
            /*Sum data for each delay point to average*/
            sum_dataI[j] += (int32_t)(data_iq->i);
            sum_dataQ[j] += (int32_t)(data_iq->q);
            /*This stuff is only for Qkit progress bar*/

            rtos_SetProgress(i * nop + j + 1);
        }
    }

    rtos_FinishDataBox(sum_dataI);
    rtos_FinishDataBox(sum_dataQ);

    // Important to free the cells at the end to not generate a memory leak!
    cells_free(cells);
    return 42;
}
