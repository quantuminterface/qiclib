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

#include "mem_io.h"

#define TEMP_MEM_SIZE 4096

int task_entry(void)
{
    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t test_code = param_list[0];
    uint32_t iterations = param_list[1];

    uint32_t *data = (uint32_t *)rtos_GetDataBox(iterations * sizeof(uint32_t));

    void *temp_memory0 = rtos_GetDataBox(TEMP_MEM_SIZE);

    // For some reasons the first calls of these functions sometimes take longer...
    // -> call them here twice in order to ensure that everything is deterministic afterwards
    rtos_EnterCriticalSection();
    rtos_RestartTimer();
    rtos_GetNsTimer();
    rtos_ExitCriticalSection();
    rtos_EnterCriticalSection();
    rtos_RestartTimer();
    rtos_GetNsTimer();
    rtos_ExitCriticalSection();

    for (uint32_t i=0; i<iterations; i++)
    {
        rtos_EnterCriticalSection();
        switch (test_code)
        {
        // Do nothing (determine overhead by measurement)
        case 0:
            rtos_RestartTimer();

            //Do nothing

            data[i] = rtos_GetNsTimer();
            break;

        // AXI4Lite Register read
        case 1:
            rtos_RestartTimer();

            ioread32(0xAA200000);

            data[i] = rtos_GetNsTimer();
            break;

        // AXI4Lite Register write
        case 2:
            rtos_RestartTimer();

            iowrite32(0xAA200040, 42);

            data[i] = rtos_GetNsTimer();
            break;

        // Memcopy 1024 registers into DRAM
        case 3:
            rtos_RestartTimer();

            memcpy(temp_memory0, (void *)0xAA202000, TEMP_MEM_SIZE);

            data[i] = rtos_GetNsTimer();
            break;

        // AXI4Lite Register read (R5 LPD)
        case 4:
            rtos_RestartTimer();

            ioread32(0x80000000);

            data[i] = rtos_GetNsTimer();
            break;

        // AXI4Lite Register write (R5 LPD)
        case 5:
            rtos_RestartTimer();

            iowrite32(0x80000040, 42);

            data[i] = rtos_GetNsTimer();
            break;

        // Memcopy 1024 registers into DRAM (R5 LPD)
        case 6:
            rtos_RestartTimer();

            memcpy(temp_memory0, (void *)0x80002000, TEMP_MEM_SIZE);

            data[i] = rtos_GetNsTimer();
            break;


        // Default action stops task -> not intended to use
        default:
            rtos_PrintfError("Unknown test no. %d", test_code);
            return 1;
        }
        rtos_ExitCriticalSection();
        rtos_SetProgress(i+1);
    }

    rtos_FinishDataBox(data);
    rtos_DiscardDataBox(temp_memory0);
    return 0;
}
