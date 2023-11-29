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
	if (param_count < 4)
	{
		rtos_PrintfError("This task needs atleast 4 parameter values (only %d given).", param_count);
		return -1;
	}
	uint32_t repetitions = param_list[0]; // How many repetitions to perform
	uint32_t cell_num = param_list[1];	  // How many cells need to be addressed
	if (param_count != 2 + 2 * cell_num)
	{
		rtos_PrintfError("This task needs exactly %d parameter values (%d given).", 2 + 2 * cell_num, param_count);
		return -1;
	}
	uint32_t *cell_list_param = &(param_list[2]);	 // The indices of the cells which should be addressed
	uint32_t *lengths = &(param_list[2 + cell_num]); // How many values a single sequencer execution returns for each cell

	// Verify the parameters
	uint8_t cell_list[cell_num];
	uint8_t cell_count = cells_get_count();
	uint32_t max_length = 0;
	for (int c = 0; c < cell_num; c++)
	{
		// Check if the cell index is valid (within range of available cells)
		if (cell_list_param[c] >= cell_count)
		{
			rtos_PrintfError(
				"Requested cell %d, but only 0 to %d available.",
				cell_list_param[c],
				cell_count - 1);
			return 1;
		}
		// Copy from 32bit to 8bit unsigned
		cell_list[c] = (uint8_t)cell_list_param[c];

		// Check if cell requests more memory than the BRAM of the recording module can hold
		if (lengths[c] > 1024)
		{
			// Limitation by the BRAM within the recording module
			rtos_PrintfError("Only 1024 values can be stored within one run, but %d requested for cell %d.", lengths[c], cell_list[c]);
			return -1;
		}

		if (lengths[c] > max_length)
			max_length = lengths[c];
	}

	// Fetch cell pointers from platform (do not forget to free at the end!)
	Cell *cells = cells_create();
	Cell cell[cell_num];
	for (uint32_t c = 0; c < cell_num; c++)
	{
		cell[c] = cells[cell_list[c]];
	}

	// Memory to temporarily store the resulting values
	//struct iq_pair_raw data_iq_raw[1024]; // Stack currently to small for this
	struct iq_pair_raw *data_iq_raw = rtos_GetDataBox(max_length * sizeof(struct iq_pair_raw));

	// Initialize the databoxes
	struct iq_pair_raw *data[cell_num][max_length];
	for (int c = 0; c < cell_num; c++)
	{
		for (int n = 0; n < lengths[c]; n++)
		{
			data[c][n] = rtos_GetDataBox(repetitions * sizeof(struct iq_pair_raw));
		}
	}

	// Wait for potential previous task
	cells_wait_while_busy();

	for (uint32_t i = 0; i < repetitions; i++)
	{
		// Synchronously start all relevant cells
		cells_start(cell_list, cell_num);

		cells_wait_while_busy();

		// Fetch the result memory
		for (int c = 0; c < cell_num; c++)
		{
			// Check that the memory holds the right amount of values (length)
			uint16_t size = rec_get_result_memory_size(cell[c].recording);
			if (size != lengths[c])
			{
				rtos_PrintfError("Expected %d result values but got %d (from cell %d). Aborting.", lengths[c], size, cell_list[c]);
				cells_free(cells);
				return -1;
			}

			// TODO Replace this with direct adding to the data boxes without intermediate copy to TCM (faster)
			rec_get_result_memory(cell[c].recording, data_iq_raw, lengths[c]);
			for (int n = 0; n < lengths[c]; n++)
			{
				data[c][n][i] = data_iq_raw[n];
			}
		}

		rtos_SetProgress(i + 1);
	}

	// Databox was only temporary -> discard it without sending back
	rtos_DiscardDataBox(data_iq_raw);

	for (int c = 0; c < cell_num; c++)
	{
		for (int n = 0; n < lengths[c]; n++)
		{
			rtos_FinishDataBox(data[c][n]);
		}
	}

	// Important to free the cells at the end to not generate a memory leak!
	cells_free(cells);
	return 0;
}
