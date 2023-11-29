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

int task_entry(void)
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t test_code = param_list[0];
    uint32_t iterations = param_list[1];

    uint32_t *data = (uint32_t *)rtos_GetDataBox(sizeof(uint32_t));

    // For some reasons the first calls of these functions sometimes take longer...
    // -> call them here twice in order to ensure that everything is deterministic afterwards
    // => Caching effects
    rtos_EnterCriticalSection();
    rtos_RestartTimer();
    rtos_GetNsTimer();
    rtos_ExitCriticalSection();
    rtos_EnterCriticalSection();
    rtos_RestartTimer();
    rtos_GetNsTimer();
    rtos_ExitCriticalSection();

    rtos_RestartTimer();
    switch (test_code)
    {
    // Do nothing (determine overhead by measurement)
    case 0:
        for (int i = 0; i < iterations; i++)
        {
            rtos_SetProgress(i+1);
        }
        break;

    // Default action stops task -> not intended to use
    default:
        rtos_ReportError("test_code not recognized!");
        return 1;
    }

    data[0] = rtos_GetNsTimer();
    rtos_FinishDataBox(data);

    return 0;
}
