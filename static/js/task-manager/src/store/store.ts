import { configureStore } from '@reduxjs/toolkit';
import taskReducer from './slices/taskSlice';
import dailySummaryReducer from './slices/dailySummarySlice';

export const store = configureStore({
  reducer: {
    tasks: taskReducer,
    dailySummary: dailySummaryReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;