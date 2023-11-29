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

int task_entry(void)
{
	xil_printf("\r\nStart Active Cooling Task\r\n");

	uint32_t *param_list = (uint32_t *)rtos_GetParameters();
	uint32_t experiment_pc = param_list[0];
	uint32_t cooling_pc = param_list[1];
	uint32_t reset_pulses = param_list[2];
	uint32_t averages = param_list[3];
	xil_printf("\r\nPCs: (%d, %d), Perform %d reset pulses and %d averages\r\n", experiment_pc, cooling_pc, reset_pulses, averages);

	struct iq_pair *single_iq = rtos_GetDataBox(sizeof(iq_pair));
	struct iq_pair *data_iq = rtos_GetDataBox(averages * sizeof(iq_pair));

	int avg = 0;
	for (avg = 0; avg < averages; avg++)
	{
		//xil_printf("\r\nExperiment finished, start cooling loop.\r\n");
		int clg = 0;
		for (clg = 0; clg < reset_pulses; clg++)
		{
			// Wait until experiment finished and T_rep is over
			seq_wait_while_busy();
			// Start cooling process in the loop
			seq_start_at(cooling_pc);
		}

		// At the beginning we once wait until sequencer has finished possible previous task
		seq_wait_while_busy();

		// Start experiment execution
		seq_start_at(experiment_pc);
		// Wait until experiment finished and T_rep is over
		seq_wait_while_busy();
		rec_wait_while_busy(0);

		// Indicate that experiment has finished and provide data
		rec_get_averaged_result(0, single_iq);
		// Averaging
		data_iq->i = data_iq->i + single_iq->i;
		data_iq->q = data_iq->q + single_iq->q;

		//sequencer_wait_until_qubit_relaxed();

		rtos_SetProgress(avg);
	}
	xil_printf("\r\nTask finished.\r\n");
	return 42;

	rtos_FinishDataBox(data_iq);
}
