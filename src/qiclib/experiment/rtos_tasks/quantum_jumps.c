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
	xil_printf("\r\nStart Quantum Jump Collection Task\r\n");

	uint32_t *param_list = (uint32_t *)rtos_GetParameters();
	uint32_t repetitions = param_list[0];

	// Fetch cell pointers from platform (do not forget to free at the end!)
	Cell *cells = cells_create();
	// Select relevant cell
	uint8_t cell_idx = 0;
	Cell cell = cells[cell_idx];

	xil_printf("Do %d repetitions.\r\n", repetitions);

	// At the beginning we once wait until sequencer has finished possible previous task
	cells_wait_while_busy();

	uint8_t *data_bytes = rtos_GetDataBox(repetitions * sizeof(int32_t));

	uint8_t states;

	uint32_t i;
	for (i = 0; i < repetitions; i += 8)
	{
		states = 0;

		uint8_t bit = 0;
		for (bit = 0; bit < 8; bit++)
		{
			seq_start_at(cell.sequencer, 0);
			// Wait until sequencer has finished and recording module has the result
			cells_wait_while_cell_busy(cell_idx);

			// Save the calculated state
			if (rec_get_state_result(cell.recording))
			{
				// State |1> detected
				states |= (1 << bit); // Set the "bit"-th bit to 1
			}
		}

		// Store states to data
		data_bytes[i] = states;
		rtos_SetProgress(i + 1);
	}

	rtos_FinishDataBox(data_bytes);

	// Important to free the cells at the end to not generate a memory leak!
	cells_free(cells);
	xil_printf("\r\nTask finished.\r\n");
	return 0;
}
