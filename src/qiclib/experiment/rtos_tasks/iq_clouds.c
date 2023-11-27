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
	uint32_t *param_list = rtos_GetParameters();
	uint32_t param_count = rtos_GetParametersSize() / sizeof(uint32_t);
	if (param_count != 2)
	{
		rtos_PrintfError("Please provide exactly 2 parameters (%d given).", param_count);
		return -1;
	}
	uint32_t repetitions = param_list[0];
	uint32_t start_pc = param_list[1];

	// Fetch cell pointers from platform (do not forget to free at the end!)
	Cell *cells = cells_create();
	// Select relevant cell
	uint8_t cell_idx = 0;
	Cell cell = cells[cell_idx];

	iq_pair *data_iq = rtos_GetDataBox(repetitions * sizeof(iq_pair));

	// Wait for potential previous task
	cells_wait_while_busy();

	for (uint32_t i = 0; i < repetitions; i++)
	{
		seq_start_at(cell.sequencer, start_pc);

		// Wait until result available
		cells_wait_while_cell_busy(cell_idx);

		rec_get_averaged_result(cell.recording, data_iq + i);

		rtos_SetProgress(i + 1);
	}

	// Important to free the cells at the end to not generate a memory leak!
	cells_free(cells);
	rtos_FinishDataBox(data_iq);
	return 0;
}
