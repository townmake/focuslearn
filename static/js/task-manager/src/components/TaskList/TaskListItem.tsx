import React from 'react';
import { useDispatch } from 'react-redux';
import { Draggable } from 'react-beautiful-dnd';
import { Card, Typography, Button, List } from 'antd';
import {
  DownOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined
} from '@ant-design/icons';
import TaskItem from './TaskItem';
import { deleteTaskList } from '@store/slices/taskListSlice';
import { useTaskDialog } from '@hooks/useTaskDialog';
import { useConfirmDialog } from '@hooks/useConfirmDialog';
import styled from 'styled-components';

const ListHeader = styled.div`
  display: flex;
  align-items: center;
  padding: 8px;
  background-color: ${props => props.color || '#fff'};
  border-radius: 4px 4px 0 0;
`;

interface TaskListItemProps {
  list: {
    id: string;
    name: string;
    color: string;
    tasks: Array<{
      id: string;
      title: string;
      is_completed: boolean;
    }>;
  };
}

const TaskListItem: React.FC<TaskListItemProps> = ({ list }) => {
  const dispatch = useDispatch();
  const [expanded, setExpanded] = React.useState(true);
  const { openDialog: openTaskDialog } = useTaskDialog();
  const { openDialog: openConfirmDialog } = useConfirmDialog();

  const handleDelete = () => {
    openConfirmDialog({
      title: '删除任务列表',
      content: '确定要删除此任务列表吗？所有相关任务都将被删除。',
      onConfirm: () => dispatch(deleteTaskList(list.id))
    });
  };

  const handleAddTask = () => {
    openTaskDialog({
      taskListId: list.id
    });
  };

  return (
    <Card 
      style={{ marginBottom: 16 }}
      bodyStyle={{ padding: 0 }}
    >
      <ListHeader color={list.color}>
        <Button
          type="text"
          icon={<DownOutlined rotate={expanded ? 180 : 0} />}
          onClick={() => setExpanded(!expanded)}
        />
        <Typography.Text strong style={{ flex: 1, marginLeft: 8 }}>
          {list.name}
        </Typography.Text>
        <Button
          type="text"
          icon={<PlusOutlined />}
          onClick={handleAddTask}
        />
        <Button
          type="text"
          icon={<EditOutlined />}
        />
        <Button
          type="text"
          icon={<DeleteOutlined />}
          onClick={handleDelete}
        />
      </ListHeader>

      {expanded && (
        <List style={{ padding: 0 }}>
          {list.tasks.map((task, index) => (
            <Draggable
              key={task.id}
              draggableId={task.id}
              index={index}
            >
              {(provided) => (
                <div
                  ref={provided.innerRef}
                  {...provided.draggableProps}
                  {...provided.dragHandleProps}
                >
                  <TaskItem task={task} />
                </div>
              )}
            </Draggable>
          ))}
        </List>
      )}
    </Card>
  );
};

export default TaskListItem;