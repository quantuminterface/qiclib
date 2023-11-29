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
#include <stdlib.h>
#include <math.h>
#include "task.h"

#include "recording.h"
//#include "sequencer.h"
#include "sequencer.h"
#include "pulsegen.h"

#include "mem_io.h"

uint32_t max(uint32_t var[], uint32_t count)
{
    int z;
    uint32_t max = 0;
    for (z = 0; z < count; z++)
    {
        if (var[z] > max)
        {
            max = var[z];
        }
    }
    return (max);
}

float mean(uint32_t var[], uint32_t count)
{
    int z;
    uint32_t sum = 0;
    float mean = 0;
    for (z = 0; z < count; z++)
    {
        sum = sum + var[z];
    }
    mean = sum / count;
    return (mean);
}
float variance(uint32_t var[], uint32_t count, float mean)
{
    int z;
    float varian = 0;
    for (z = 0; z < count; z++)
    {
        varian = varian + pow((mean - var[z]), 2);
    }
    varian = varian / (count);
    varian = sqrt(varian);
    return (varian);
}

uint8_t ioread8(uint32_t addr)
{
    uint8_t *ptr = (uint8_t *)((char *)addr);
    return *ptr;
}

void iowrite8(uint32_t addr, uint8_t value)
{
    uint8_t *ptr = (uint8_t *)((char *)addr);
    *ptr = value;
}

void manualCopy32(uint32_t *pDest, uint32_t *pSrc, uint32_t len)
{
    uint32_t i;

    // Manually copy the data
    for (i = 0; i < len; i++)
    {
        // Copy data from source to destination
        *pDest++ = *pSrc++;
    }
}

int task_entry()
{
    //Xil_ICacheDisable();
    //Xil_DCacheDisable();
    int i;

    void sysFastMemCopy(uint8_t * pDest, uint8_t * pSrc, uint32_t len);
    void manualCopy(uint8_t * pDest, uint8_t * pSrc, uint32_t len);

    uint32_t *param_list = (uint32_t *)rtos_GetParameters();
    uint32_t test_code = param_list[0];
    uint32_t iterations = param_list[1];

    uint32_t *data = (uint32_t *)rtos_GetDataBox((iterations + 4) * sizeof(uint32_t));

    uint32_t *addr = (uint32_t *)rtos_GetDataBox(4096);
    uint8_t *addr8 = (uint8_t *)addr;
    uint32_t *src = (uint32_t *)0xaa208000;
    uint8_t *src8 = (uint8_t *)src;

    uint32_t val;

    int ar_len = 1024;
    int32_t *array1 = (int32_t *)rtos_GetDataBox(4096);
    int32_t *array2 = (int32_t *)rtos_GetDataBox(4096);
    int ar_len2 = ar_len * 2;
    int16_t *array1_16 = (int16_t *)rtos_GetDataBox(4096);
    int16_t *array2_16 = (int16_t *)rtos_GetDataBox(4096);

    if (test_code == 13 || test_code == 14)
    {
        for (i = 0; i < ar_len; i++)
        {
            array1[i] = rand() % 100 + 1;
            array2[i] = rand() % 100 + 1;
        }

        for (i = 0; i < ar_len2; i++)
        {
            array1_16[i] = rand() % 100 + 1;
            array2_16[i] = rand() % 100 + 1;
        }
    }

    switch (test_code)
    {

    case 0:
        for (i = 0; i < iterations; i++)
        {
            //rtos_EnterCriticalSection();
            //rtos_RestartTimer();

            //Do nothing

            //val = rtos_GetNsTimer();
            //rtos_ExitCriticalSection();
            //data[i]=val*2;
            rtos_SetProgress(i + 1);
        }
        break;

    case 1:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            ioread32(0xAA000000);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = 2 * val;
            rtos_SetProgress(i + 1);
        }
        break;

    case 2:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            iowrite32(0xAA110040, 0);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = 2 * val;
            rtos_SetProgress(i + 1);
        }
        break;

    case 3:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            rtos_SetProgress(i + 1);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
        }
        break;

    case 4:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            seq_is_busy();

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;
    case 5:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            seq_get_averages();
            // seq_get_status_reg();

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;

    case 6:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            //memcpy (&(data[iterations+5+i]), src ,4096);
            memcpy(addr, src, 4096);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;

    case 7:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            //sysFastMemCopy((uint8_t*)&(data[iterations+5+i]), (uint8_t*)src ,4096);
            sysFastMemCopy(addr8, src8, 4096);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;
    case 8:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            //manualCopy((uint8_t*)&(data[iterations+5+i]), (uint8_t*)src ,4096);
            manualCopy(addr8, src8, 4096);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;
    case 9:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            ioread8(0xAA000000);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;

    case 10:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            iowrite8(0xAA110040, 0);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;

    case 11:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            ioread32(0x99);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;

    case 12:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            rtos_RestartTimer();

            manualCopy32(addr, src, 1024);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;

    case 13:
        for (i = 0; i < iterations; i++)
        {
            int n;
            int64_t s = 0;
            rtos_EnterCriticalSection();
            rtos_RestartTimer();
            for (n = 0; n < ar_len; n++)
            {
                s += array1[n] * array2[n];
            }
            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            data[iterations + 5] = s;
            rtos_SetProgress(i + 1);
        }
        break;
    case 14:
        for (i = 0; i < iterations; i++)
        {
            int n;
            int64_t s = 0;
            rtos_EnterCriticalSection();
            rtos_RestartTimer();
            for (n = 0; n < ar_len2; n++)
            {
                s += array1_16[n] * array2_16[n];
            }
            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            data[iterations + 6] = s;
            rtos_SetProgress(i + 1);
        }
        break;
    case 16:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            uint32_t a = PULSEGEN_MANIP_ADDR_OFFSET + PULSEGEN_ENV_MEMORY;
            rtos_RestartTimer();

            pulsegen_write32(a, 0);

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;
    case 18:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            uint32_t number;
            int des = iterations + 4;
            rtos_RestartTimer();

            number = data[des];

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            number = number + 1;
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;
    case 19:
        for (i = 0; i < iterations; i++)
        {
            rtos_EnterCriticalSection();
            int des1 = iterations + 4;
            int des2 = des1 + 1;
            data[des2] = 0;
            rtos_RestartTimer();
            data[des1] = data[des2];

            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            rtos_SetProgress(i + 1);
        }
        break;

    case 17:
        for (i = 0; i < iterations; i++)
        {
            uint16_t *na;
            na = pg_register_pulse(0, 100, 0);
            rtos_EnterCriticalSection();
            rtos_RestartTimer();
            pg_write_rect_pulse(na, 100);
            val = rtos_GetNsTimer();
            rtos_ExitCriticalSection();
            data[i] = val * 2;
            pg_reset_envelope_memory();
            rtos_SetProgress(i + 1);
        }
        break;

        /*         case 15:
            for (i=0; i<iterations; i++){
                rtos_SetProgress(0);
            }
            break; */

    default:
        return 1;
    }

    data[iterations + 1] = max(data, iterations);
    data[iterations + 2] = (uint32_t)mean(data, iterations);
    data[iterations + 3] = (uint32_t)variance(data, iterations, mean(data, iterations));

    rtos_FinishDataBox(data);

    rtos_DiscardDataBox(addr);
    rtos_DiscardDataBox(array1);
    rtos_DiscardDataBox(array2);
    rtos_DiscardDataBox(array1_16);
    rtos_DiscardDataBox(array2_16);

    return 0;
}

/******************************************************************************
 *
 * Function Name:  manualCopy
 *
 * Description: Manually copies data from memory to memory.  This is used by
 * sysFastMemCopy to copy a few lingering bytes at the beginning and end.
 *
 *****************************************************************************/

inline void manualCopy(uint8_t *pDest, uint8_t *pSrc, uint32_t len)
{
    uint32_t i;

    // Manually copy the data
    for (i = 0; i < len; i++)
    {
        // Copy data from source to destination
        *pDest++ = *pSrc++;
    }
}

/******************************************************************************
 *
 * Function Name:  sysFastMemCopy
 *
 * Description: Assuming that your processor can do 32-bit memory accesses
 * and contains a barrel shifter and that you are using an efficient
 * compiler, then this memory-to-memory copy procedure will probably be more
 * efficient than just using the traditional memcpy procedure if the number
 * of bytes to copy is greater than about 20.  It works by doing 32-bit
 * reads and writes instead of using 8-bit memory accesses.
 *
 * NOTE that this procedure assumes a Little Endian processor!  The shift
 * operators ">>" and "<<" should all be reversed for Big Endian.
 *
 * NEVER use this when the number of bytes to be copied is less than about
 * 10, since it may not work for a small number of bytes.  Also, do not use
 * this when the source and destination regions overlap.
 *
 * NOTE that this may NOT be faster than memcpy if your processor supports a
 * really fast cache memory!
 *
 * Timing for this sysFastMemCopy varies some according to which shifts need
 * to be done.  The following results are from one attempt to measure timing
 * on a Cortex M4 processor running at 48 MHz.
 *
 *                           MEMCPY        FAST
 *                  BYTES  bytes/usec   bytes/usec
 *                  -----  ----------  ------------
 *                    50       4.2      6.3 to  6.3
 *                   100       4.5      8.3 to 10.0
 *                   150       4.8     10.0 to 11.5
 *                   200       4.9     10.5 to 12.5
 *                   250       5.1     11.4 to 13.2
 *                   300       5.1     11.5 to 13.6
 *                   350       5.1     12.1 to 14.6
 *                   400       5.1     12.1 to 14.8
 *                   450       5.2     12.2 to 15.5
 *                   500       5.2     12.5 to 15.2
 *
 * The following macro can be used instead of memcpy to automatically select
 * whether to use memcpy or sysFastMemCopy:
 *
 *   #define MEMCOPY(pDst,pSrc,len) \
 *     (len) < 16 ? memcpy(pDst,pSrc,len) : sysFastMemCopy(pDst,pSrc,len);
 *
 *****************************************************************************/

void sysFastMemCopy(uint8_t *pDest, uint8_t *pSrc, uint32_t len)
{
    uint32_t srcCnt;
    uint32_t destCnt;
    uint32_t newLen;
    uint32_t endLen;
    uint32_t longLen;
    uint32_t *pLongSrc;
    uint32_t *pLongDest;
    uint32_t longWord1;
    uint32_t longWord2;
    uint32_t methodSelect;

    // Determine the number of bytes in the first word of src and dest
    srcCnt = 4 - ((uint32_t)pSrc & 0x03);
    destCnt = 4 - ((uint32_t)pDest & 0x03);

    // Copy the initial bytes to the destination
    manualCopy(pDest, pSrc, destCnt);

    // Determine the number of bytes remaining
    newLen = len - destCnt;

    // Determine how many full long words to copy to the destination
    longLen = newLen / 4;

    // Determine number of lingering bytes to copy at the end
    endLen = newLen & 0x03;

    // Pick the initial long destination word to copy to
    pLongDest = (uint32_t *)(pDest + destCnt);

    // Pick the initial source word to start our algorithm at
    if (srcCnt <= destCnt)
    {
        // Advance to pSrc at the start of the next full word
        pLongSrc = (uint32_t *)(pSrc + srcCnt);
    }
    else // There are still source bytes remaining in the first word
    {
        // Set pSrc to the start of the first full word
        pLongSrc = (uint32_t *)(pSrc + srcCnt - 4);
    }

    // There are 4 different longWord copy methods
    methodSelect = (srcCnt - destCnt) & 0x03;

    // Just copy one-to-one
    if (methodSelect == 0)
    {
        // Just copy the specified number of long words
        while (longLen-- > 0)
        {
            *pLongDest++ = *pLongSrc++;
        }
    }
    else if (methodSelect == 1)
    {
        // Get the first long word
        longWord1 = *pLongSrc++;

        // Copy words created by combining 2 adjacent long words
        while (longLen-- > 0)
        {
            // Get the next 32-bit word
            longWord2 = *pLongSrc++;

            // Write to the destination
            *pLongDest++ = (longWord1 >> 24) | (longWord2 << 8);

            // Re-use the word just retrieved
            longWord1 = longWord2;
        }
    }
    else if (methodSelect == 2)
    {
        // Get the first long word
        longWord1 = *pLongSrc++;

        // Copy words created by combining 2 adjacent long words
        while (longLen-- > 0)
        {
            // Get the next 32-bit word
            longWord2 = *pLongSrc++;

            // Write to the destination
            *pLongDest++ = (longWord1 >> 16) | (longWord2 << 16);

            // Re-use the word just retrieved
            longWord1 = longWord2;
        }
    }
    else // ( methodSelect == 3 )
    {
        // Get the first long word
        longWord1 = *pLongSrc++;

        // Copy words created by combining 2 adjacent long words
        while (longLen-- > 0)
        {
            // Get the next 32-bit word
            longWord2 = *pLongSrc++;

            // Write to the destination
            *pLongDest++ = (longWord1 >> 8) | (longWord2 << 24);

            // Re-use the word just retrieved
            longWord1 = longWord2;
        }
    }

    // Copy any remaining bytes
    if (endLen != 0)
    {
        // The trailing bytes will be copied next
        pDest = (uint8_t *)pLongDest;

        // Determine where the trailing source bytes are located
        pSrc += len - endLen;

        // Copy the remaining bytes
        manualCopy(pDest, pSrc, endLen);
    }
}
