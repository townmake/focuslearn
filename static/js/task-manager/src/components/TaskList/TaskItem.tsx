import React from 'react';
import { useDispatch } from 'react-redux';
import { List, Checkbox, Button, Tooltip, Typography } from 'antd';
import {
  DeleteOutlined,
  EditOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { toggleTaskComplete, deleteTask } from '@store/slices/taskSlice';
import { useTaskDialog } from '@hooks/useTaskDialog';
import { useConfirmDialog } from '@hooks/useConfirmDialog';
import styled from 'styled-components';

const TaskListItem = styled(List.Item)`
  padding: 8px 16px;
  border-bottom: 1px solid #eee;
  &:hover {
    background-color: #f9f9f9;
  }
`;

const CompletedText = styled(Typography.Text)`
  text-decoration: line-through;
  color: #888;
`;

interface TaskItemProps {
  task: {
    id: string;
    title: string;
    is_completed: boolean;
  };
}

const TaskItem: React.FC<TaskItemProps> = ({ task }) => {
  const dispatch = useDispatch();
  const { openDialog: openTaskDialog } = useTaskDialog();
  const { openDialog: openConfirmDialog } = useConfirmDialog();

  const handleToggleComplete = () => {
    dispatch(toggleTaskComplete(task.id));
  };

  const handleEdit = () => {
    openTaskDialog({
      task
    });
  };

  const handleDelete = () => {
    openConfirmDialog({
      title: '删除任务',
      content: '确定要删除此任务吗？',
      onConfirm: () => dispatch(deleteTask(task.id))
    });
  };

  const handleDragToCalendar = (e: React.DragEvent) => {
    e.dataTransfer.setData('task', JSON.stringify(task));
  };

  return (
    <TaskListItem
      draggable
      onDragStart={handleDragToCalendar}
      actions={[
        <Tooltip title="日历视图">
          <Button type="text" icon={<CalendarOutlined />} size="small" />
        </Tooltip>,
        <Tooltip title="编辑任务">
          <Button type="text" icon={<EditOutlined />} size="small" onClick={handleEdit} />
        </Tooltip>,
        <Tooltip title="删除任务">
          <Button type="text" icon={<DeleteOutlined />} size="small" onClick={handleDelete} />
        </Tooltip>
      ]}
    >
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Checkbox
          checked={task.is_completed}
          onChange={handleToggleComplete}
          style={{ marginRight: 8 }}
        />
        {task.is_completed ? (
          <CompletedText>{task.title}</CompletedText>
        ) : (
          <Typography.Text>{task.title}</Typography.Text>
        )}
      </div>
    </TaskListItem>
  );
};

export default TaskItem;