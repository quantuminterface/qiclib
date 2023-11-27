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
// Rabi experiment task. Iteration averaging is done. The new waveform is generated and load from R5 for each pulse duration
#include <string.h>

#include "task.h"
#include "recording.h"
#include "sequencer.h"
#include "pulsegen.h"

int task_entry(void)
{
    int i, j;

    uint32_t *param_list = (uint32_t *)rtos_GetParameters();

    uint32_t iterations = (param_list++)[0];
    uint32_t drag_amplitude = (param_list++)[0];
    uint32_t nop = (param_list++)[0];

    uint32_t durations[nop];
    for (i = 0; i < nop; i++)
    {
        durations[i] = (param_list++)[0];
    }

    int32_t *sum_dataI = rtos_GetDataBox(nop * sizeof(int32_t));
    int32_t *sum_dataQ = rtos_GetDataBox(nop * sizeof(int32_t));

    iq_pair *data_iq = rtos_GetDataBox(sizeof(iq_pair));

    float sigma_duration_ratio = 0.37;

    for (j = 0; j < nop; j++)
    {
        sum_dataI[j] = 0;
        sum_dataQ[j] = 0;
    }

    seq_wait_while_busy(); //wait for previous task to finish

    for (i = 0; i < iterations; i++)
    {
        for (j = 0; j < nop; j++)
        {

            pg_write_gauss_pulse(pg_register_pulse(0, durations[j], PULSEGEN_CHANNEL_Q),
                                 durations[j],
                                 sigma_duration_ratio * durations[j]);

            pg_write_gauss_derivative_pulse(pg_register_pulse(0, durations[j], PULSEGEN_CHANNEL_I),
                                            durations[j],
                                            sigma_duration_ratio * durations[j],
                                            drag_amplitude / PULSEGEN_MAX_POS_VALUE);

            seq_set_register(1, durations[j]);

            seq_start_at(0);

            seq_wait_while_busy();
            rec_wait_while_busy(0);
            rec_get_averaged_result(0, data_iq);

            sum_dataI[j] += (int32_t)(data_iq->i);
            sum_dataQ[j] += (int32_t)(data_iq->q);

            pg_reset_envelope_memory();
        }
    }

    rtos_FinishDataBox(sum_dataI);
    rtos_FinishDataBox(sum_dataQ);

    return 42;
}
