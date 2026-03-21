import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import { Typography, Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import TaskListItem from './TaskListItem';
import { selectTaskLists } from '@store/slices/taskListSlice';
import { moveTask } from '@store/slices/taskSlice';
import { useTaskListDialog } from '@hooks/useTaskListDialog';
import styled from 'styled-components';

const TaskListWrapper = styled.div`
  width: 300px;
  height: 100%;
  padding: 16px;
  overflow-y: auto;
  background-color: #f5f5f5;
  border-radius: 2px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
`;

const TaskListContainer: React.FC = () => {
  const dispatch = useDispatch();
  const taskLists = useSelector(selectTaskLists);
  const { openDialog } = useTaskListDialog();

  const handleDragEnd = (result: any) => {
    if (!result.destination) return;

    const sourceId = result.source.droppableId;
    const destId = result.destination.droppableId;
    const taskId = result.draggableId;

    dispatch(moveTask({
      taskId,
      sourceListId: sourceId,
      destinationListId: destId,
      sourceIndex: result.source.index,
      destinationIndex: result.destination.index
    }));
  };

  return (
    <TaskListWrapper>
      <Header>
        <Typography.Title level={5} style={{ margin: 0 }}>任务列表</Typography.Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => openDialog()}
          size="small"
        >
          新建列表
        </Button>
      </Header>
      
      <DragDropContext onDragEnd={handleDragEnd}>
        {taskLists.map((list) => (
          <Droppable key={list.id} droppableId={list.id}>
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
              >
                <TaskListItem list={list} />
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        ))}
      </DragDropContext>
    </TaskListWrapper>
  );
};

export default TaskListContainer;