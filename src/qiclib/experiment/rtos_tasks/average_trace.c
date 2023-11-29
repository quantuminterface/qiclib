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
#include "cells.h"

int task_entry(void)
{
    // Fetch parameters from user
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t averages = param_list[0];
    uint32_t offset = param_list[1];
    uint32_t size = param_list[2];
    uint8_t cell_index = param_list[3];

    // Check if the parameters are valid
    uint8_t cell_count = cells_get_count();
    if (cell_index >= cell_count)
    {
        rtos_PrintfError(
            "Requested cell %d, but only 0 to %d available.",
            cell_index,
            cell_count - 1);
        return 1;
    }

    // Fetch cell pointers from platform (do not forget to free at the end!)
    Cell *cells = cells_create();
    // Select relevant cell
    Cell cell = cells[cell_index];

    // Set configuration of recording module
    rec_set_trigger_offset(cell.recording, offset);
    rec_set_recording_duration(cell.recording, size);

    // Create temporary data array to fetch raw results
    // This can lead to a stack overflow:
    //struct iq_pair_raw data_iq_raw[size];
    // Use temporary Databox for now instead:
    struct iq_pair_raw *data_iq_raw = rtos_GetDataBox(size * sizeof(struct iq_pair_raw));

    // Create data boxes for the final results
    // that should be transferred back to the user
    int32_t *sum_dataI = rtos_GetDataBox(size * sizeof(int32_t));
    int32_t *sum_dataQ = rtos_GetDataBox(size * sizeof(int32_t));
    // and initialize these with zeros
    for (int n = 0; n < size; n++)
    {
        sum_dataI[n] = 0;
        sum_dataQ[n] = 0;
    }

    seq_wait_while_busy(cell.sequencer); //wait for previous task to finish

    for (int i = 0; i < averages; i++)
    {
        seq_start_at(cell.sequencer, 0);

        seq_wait_while_busy(cell.sequencer);
        rec_wait_while_busy(cell.recording);

        rec_get_raw_timetrace(cell.recording, data_iq_raw, size);

        for (int n = 0; n < size; n++)
        {
            sum_dataI[n] += (int16_t)(data_iq_raw[n].i);
            sum_dataQ[n] += (int16_t)(data_iq_raw[n].q);
        }

        rtos_SetProgress(i + 1);
    }

    // Free temporary databox to avoid memory leakage
    rtos_DiscardDataBox(data_iq_raw);

    // Finish data boxes so they can be fetched by the user
    rtos_FinishDataBox(sum_dataI);
    rtos_FinishDataBox(sum_dataQ);

    // Important to free the cells at the end to not generate a memory leak!
    cells_free(cells);
    return 42;
}
