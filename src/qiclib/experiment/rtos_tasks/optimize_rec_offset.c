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

int task_entry()
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
    if (param_count != 4)
    {
        rtos_PrintfError("This task needs excactly 4 parameter values (only %d given).", param_count);
        return -1;
    }
    uint32_t cell_idx = param_list[0]; // Which cell to be addressed
    uint32_t offset_min = param_list[1];
    uint32_t offset_max = param_list[2];
    uint32_t start_pc = param_list[3];

    // Verify the parameters
    uint8_t cell_count = cells_get_count();
    if (cell_idx >= cell_count)
    {
        rtos_PrintfError(
            "Requested cell %d, but only 0 to %d available.",
            cell_idx,
            cell_count - 1);
        return 1;
    }

    uint32_t offset_len = offset_max - offset_min;
    if (offset_len <= 0)
    {
        rtos_PrintfError(
            "Maximum offset needs to be larger than minimum offset!");
        return 1;
    }
    if (offset_max > 256)
    {
        rtos_PrintfError(
            "Maximum offset cannot be larger than 1024ns!");
        return 1;
    }

    // Fetch cell pointers from platform (do not forget to free at the end!)
    Cell *cells = cells_create();
    Cell cell = cells[cell_idx];

    iq_pair *data_iq = rtos_GetDataBox(offset_len * sizeof(iq_pair));

    // Wait for previous task to finish
    cells_wait_while_busy();

    // Note: Averages need to be set in sequencer beforehand
    // seq_set_averages(cell.sequencer, averages);

    for (int i = 0; i < offset_len; i++)
    {
        // Set offset
        rec_set_trigger_offset(cell.recording, offset_min + i);

        // Synchronously start all relevant cells
        seq_start_at(cell.sequencer, start_pc);

        cells_wait_while_busy();

        rec_get_averaged_result(cell.recording, data_iq + i);

        rtos_SetProgress(i + 1);
    }

    // Important to free the cells at the end to not generate a memory leak!
    cells_free(cells);
    rtos_FinishDataBox(data_iq);
    return 0;
}
