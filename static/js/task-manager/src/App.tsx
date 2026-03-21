import React from 'react';
import { Provider } from 'react-redux';
import { ConfigProvider } from 'antd';
import { TaskListContainer } from './components/TaskList';
import CalendarContainer from './components/Calendar/CalendarContainer';
import { TaskDialog } from './components/Dialogs/TaskDialog';
import { TaskListDialog } from './components/Dialogs/TaskListDialog';
import { ConfirmDialog } from './components/Dialogs/ConfirmDialog';
import { store } from './store';
import styled from 'styled-components';

const theme = {
  token: {
    colorPrimary: '#1976d2',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    borderRadius: 2,
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
};

const AppContainer = styled.div`
  display: flex;
  height: calc(100vh - 64px);
  padding: 16px;
`;

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ConfigProvider theme={theme}>
        <AppContainer>
          <TaskListContainer />
          <CalendarContainer />
        </AppContainer>
        <TaskDialog />
        <TaskListDialog />
        <ConfirmDialog />
      </ConfigProvider>
    </Provider>
  );
};

export default App;