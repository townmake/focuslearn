import React, { useState } from 'react';
import { Box, Paper } from '@mui/material';
import styled from 'styled-components';
import CalendarView from './CalendarView';
import DailySummary from './DailySummary';

const Container = styled(Box)`
  display: flex;
  gap: 16px;
  padding: 16px;
  height: calc(100vh - 64px); // 假设顶部导航栏高度为64px
`;

const SidePanel = styled(Paper)`
  width: 300px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
`;

const CalendarContainer: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
  };

  return (
    <Container>
      <CalendarView onDateSelect={handleDateSelect} />
      <SidePanel elevation={1}>
        <DailySummary date={selectedDate} />
      </SidePanel>
    </Container>
  );
};

export default CalendarContainer;