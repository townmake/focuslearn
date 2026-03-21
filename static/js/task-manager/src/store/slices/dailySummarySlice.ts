import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';
import { RootState } from '../store';

interface DailySummary {
  id?: number;
  date: string;
  description: string;
  created_at?: string;
  updated_at?: string;
}

interface DailySummaryState {
  summaries: DailySummary[];
  loading: boolean;
  error: string | null;
}

const initialState: DailySummaryState = {
  summaries: [],
  loading: false,
  error: null,
};

// 获取指定日期范围的每日总结
export const fetchDailySummaries = createAsyncThunk(
  'dailySummary/fetchDailySummaries',
  async (dateRange: { startDate: string; endDate: string }) => {
    const response = await axios.get('/api/daily-summaries/', {
      params: {
        start_date: dateRange.startDate,
        end_date: dateRange.endDate,
      },
    });
    return response.data;
  }
);

// 创建每日总结
export const createDailySummary = createAsyncThunk(
  'dailySummary/createDailySummary',
  async (summary: { date: string; description: string }) => {
    const response = await axios.post('/api/daily-summaries/', summary);
    return response.data;
  }
);

// 更新每日总结
export const updateDailySummary = createAsyncThunk(
  'dailySummary/updateDailySummary',
  async (summary: DailySummary) => {
    const response = await axios.put(`/api/daily-summaries/${summary.id}/`, summary);
    return response.data;
  }
);

// 删除每日总结
export const deleteDailySummary = createAsyncThunk(
  'dailySummary/deleteDailySummary',
  async (id: number) => {
    await axios.delete(`/api/daily-summaries/${id}/`);
    return id;
  }
);

const dailySummarySlice = createSlice({
  name: 'dailySummary',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Daily Summaries
      .addCase(fetchDailySummaries.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDailySummaries.fulfilled, (state, action: PayloadAction<DailySummary[]>) => {
        state.loading = false;
        state.summaries = action.payload;
      })
      .addCase(fetchDailySummaries.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '获取每日总结失败';
      })
      
      // Create Daily Summary
      .addCase(createDailySummary.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createDailySummary.fulfilled, (state, action: PayloadAction<DailySummary>) => {
        state.loading = false;
        state.summaries.push(action.payload);
      })
      .addCase(createDailySummary.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '创建每日总结失败';
      })
      
      // Update Daily Summary
      .addCase(updateDailySummary.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateDailySummary.fulfilled, (state, action: PayloadAction<DailySummary>) => {
        state.loading = false;
        const index = state.summaries.findIndex(summary => summary.id === action.payload.id);
        if (index !== -1) {
          state.summaries[index] = action.payload;
        }
      })
      .addCase(updateDailySummary.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '更新每日总结失败';
      })
      
      // Delete Daily Summary
      .addCase(deleteDailySummary.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteDailySummary.fulfilled, (state, action: PayloadAction<number>) => {
        state.loading = false;
        state.summaries = state.summaries.filter(summary => summary.id !== action.payload);
      })
      .addCase(deleteDailySummary.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '删除每日总结失败';
      });
  },
});

// 导出 actions
export const { clearError } = dailySummarySlice.actions;

// 导出 selectors
export const selectDailySummaries = (state: RootState) => state.dailySummary.summaries;
export const selectDailySummaryLoading = (state: RootState) => state.dailySummary.loading;
export const selectDailySummaryError = (state: RootState) => state.dailySummary.error;

export default dailySummarySlice.reducer;