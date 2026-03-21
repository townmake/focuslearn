import React, { useState, useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import dayGridPlugin from '@fullcalendar/daygrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import { Paper, Box, Typography, IconButton, Tooltip, ButtonGroup, Button } from '@mui/material';
import { 
  ViewWeek as ViewWeekIcon, 
  ViewDay as ViewDayIcon, 
  ViewAgenda as ViewAgendaIcon,
  Today as TodayIcon
} from '@mui/icons-material';
import { selectTasks, fetchTasksByDateRange } from '@store/slices/taskSlice';
import { useTaskDialog } from '@hooks/useTaskDialog';
import styled from 'styled-components';

const CalendarWrapper = styled(Paper)`
  flex: 1;
  padding: 16px;
  margin-left: 16px;
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  
  .fc {
    height: 100%;
  }

  .fc-timegrid-slot {
    height: 48px !important;
  }

  .fc-event {
    cursor: pointer;
    border-radius: 4px;
    padding: 2px 4px;
  }
  
  .fc-event-main {
    padding: 2px;
    overflow: hidden;
  }
  
  .fc-event-title {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .fc-event-time {
    font-size: 0.85em;
    opacity: 0.8;
  }
  
  .fc-day-today {
    background-color: rgba(66, 165, 245, 0.05) !important;
  }
  
  .task-completed {
    opacity: 0.7;
    text-decoration: line-through;
  }
`;

const CalendarHeader = styled(Box)`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
`;

const ViewControls = styled(Box)`
  display: flex;
  gap: 8px;
  margin-left: 16px;
`;

const StyledButtonGroup = styled(ButtonGroup)`
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  
  .MuiButton-root {
    padding: 4px 12px;
    min-width: unset;
    
    &.active {
      background-color: #1976d2;
      color: white;
    }
  }
`;

const CalendarView: React.FC = () => {
  const dispatch = useDispatch();
  const tasks = useSelector(selectTasks);
  const { openDialog } = useTaskDialog();
  const [calendarRef, setCalendarRef] = useState<any>(null);
  const [currentView, setCurrentView] = useState<string>('timeGridWeek');
  const [currentViewLabel, setCurrentViewLabel] = useState<string>('周');
  const [dateRange, setDateRange] = useState<{start: Date, end: Date} | null>(null);

  // 日期范围变化时获取任务
  useEffect(() => {
    if (dateRange) {
      dispatch(fetchTasksByDateRange({
        startDate: dateRange.start.toISOString(),
        endDate: dateRange.end.toISOString()
      }));
    }
  }, [dateRange, dispatch]);

  // 处理日历日期范围变化
  const handleDatesSet = useCallback((arg: any) => {
    setDateRange({
      start: arg.start,
      end: arg.end
    });
  }, []);

  // 处理日期点击 - 创建新任务
  const handleDateClick = useCallback((arg: any) => {
    const endTime = new Date(arg.date);
    endTime.setHours(endTime.getHours() + 1);
    
    openDialog({
      startDate: arg.date,
      endDate: endTime
    });
  }, [openDialog]);

  // 处理事件点击 - 编辑任务
  const handleEventClick = useCallback((info: any) => {
    const task = tasks.find(t => t.id === info.event.id);
    if (task) {
      openDialog({
        task
      });
    }
  }, [tasks, openDialog]);

  // 处理拖拽事件 - 更新任务时间
  const handleEventDrop = useCallback((info: any) => {
    const taskId = info.event.id;
    const newStart = info.event.start;
    const newEnd = info.event.end || new Date(newStart.getTime() + 60 * 60 * 1000);

    dispatch({
      type: 'tasks/updateTaskTime',
      payload: {
        taskId,
        startDateTime: newStart,
        endDateTime: newEnd
      }
    });
  }, [dispatch]);

  // 处理外部元素拖入日历
  const handleDrop = useCallback((info: any) => {
    try {
      const task = JSON.parse(info.draggedEl.getAttribute('data-task'));
      const startDate = info.date;
      const endDate = new Date(startDate.getTime() + 60 * 60 * 1000); // 默认1小时
      
      openDialog({
        task: {
          ...task,
          start_datetime: startDate,
          end_datetime: endDate
        }
      });
    } catch (error) {
      console.error('Drop handling error:', error);
    }
  }, [openDialog]);

  // 处理事件渲染 - 自定义事件样式
  const handleEventContent = useCallback((eventInfo: any) => {
    const isCompleted = eventInfo.event.extendedProps.is_completed;
    
    return (
      <div className={`event-content ${isCompleted ? 'task-completed' : ''}`}>
        <div className="fc-event-time">
          {eventInfo.timeText}
        </div>
        <div className="fc-event-title">
          {eventInfo.event.title}
        </div>
        {eventInfo.event.extendedProps.description && (
          <div className="fc-event-description" style={{fontSize: '0.8em', opacity: 0.8}}>
            {eventInfo.event.extendedProps.description.substring(0, 30)}
            {eventInfo.event.extendedProps.description.length > 30 ? '...' : ''}
          </div>
        )}
      </div>
    );
  }, []);

  // 切换视图
  const changeView = (viewName: string, label: string) => {
    if (calendarRef) {
      const calendarApi = calendarRef.getApi();
      calendarApi.changeView(viewName);
      setCurrentView(viewName);
      setCurrentViewLabel(label);
    }
  };

  // 跳转到今天
  const goToToday = () => {
    if (calendarRef) {
      const calendarApi = calendarRef.getApi();
      calendarApi.today();
    }
  };

  // 格式化任务为日历事件
  const events = tasks.map(task => ({
    id: task.id,
    title: task.title,
    start: task.start_datetime,
    end: task.end_datetime,
    backgroundColor: task.task_list.color,
    borderColor: task.task_list.color,
    textColor: getContrastTextColor(task.task_list.color),
    extendedProps: {
      description: task.description,
      is_completed: task.is_completed,
      taskListId: task.task_list.id,
      taskListName: task.task_list.name
    }
  }));

  // 根据背景色计算对比色文本
  function getContrastTextColor(hexColor: string) {
    // 移除 # 符号（如果存在）
    hexColor = hexColor.replace('#', '');
    
    // 将颜色转换为 RGB
    const r = parseInt(hexColor.substr(0, 2), 16);
    const g = parseInt(hexColor.substr(2, 2), 16);
    const b = parseInt(hexColor.substr(4, 2), 16);
    
    // 计算亮度
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    
    // 如果亮度高于 128，返回黑色，否则返回白色
    return brightness > 128 ? '#000000' : '#ffffff';
  }

  return (
    <CalendarWrapper elevation={1}>
      <CalendarHeader>
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h6" component="h2" sx={{ fontWeight: 500 }}>
            学习计划日历
          </Typography>
          <ViewControls>
            <StyledButtonGroup>
              <Tooltip title="月视图">
                <Button 
                  className={currentView === 'dayGridMonth' ? 'active' : ''}
                  onClick={() => changeView('dayGridMonth', '月')}
                >
                  月
                </Button>
              </Tooltip>
              <Tooltip title="周视图">
                <Button 
                  className={currentView === 'timeGridWeek' ? 'active' : ''}
                  onClick={() => changeView('timeGridWeek', '周')}
                >
                  周
                </Button>
              </Tooltip>
              <Tooltip title="日视图">
                <Button 
                  className={currentView === 'timeGridDay' ? 'active' : ''}
                  onClick={() => changeView('timeGridDay', '日')}
                >
                  日
                </Button>
              </Tooltip>
              <Tooltip title="列表视图">
                <Button 
                  className={currentView === 'listWeek' ? 'active' : ''}
                  onClick={() => changeView('listWeek', '列表')}
                >
                  列表
                </Button>
              </Tooltip>
            </StyledButtonGroup>
          </ViewControls>
        </Box>
        <Box display="flex" alignItems="center" gap={1}>
          <Tooltip title="今天">
            <Button
              variant="contained"
              size="small"
              onClick={goToToday}
              startIcon={<TodayIcon />}
            >
              今天
            </Button>
          </Tooltip>
        </Box>
      </CalendarHeader>
      
      <FullCalendar
        ref={setCalendarRef}
        plugins={[timeGridPlugin, dayGridPlugin, listPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        headerToolbar={{
          left: 'prev,next',
          center: 'title',
          right: 'today'
        }}
        buttonText={{
          today: '今天',
          month: '月',
          week: '周',
          day: '日',
          list: '列表'
        }}
        views={{
          timeGridWeek: {
            titleFormat: { year: 'numeric', month: 'long', day: 'numeric' },
            dayHeaderFormat: { weekday: 'short', month: 'numeric', day: 'numeric', omitCommas: true }
          },
          timeGridDay: {
            titleFormat: { year: 'numeric', month: 'long', day: 'numeric' }
          },
          dayGridMonth: {
            titleFormat: { year: 'numeric', month: 'long' }
          },
          listWeek: {
            titleFormat: { year: 'numeric', month: 'long' }
          }
        }}
        slotMinTime="06:00:00"
        slotMaxTime="24:00:00"
        allDaySlot={false}
        editable={true}
        droppable={true}
        events={events}
        eventClick={handleEventClick}
        eventDrop={handleEventDrop}
        dateClick={handleDateClick}
        drop={handleDrop}
        datesSet={handleDatesSet}
        eventContent={handleEventContent}
        locale="zh-cn"
        firstDay={1}
        slotLabelFormat={{
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        }}
        dayMaxEvents={true}
        nowIndicator={true}
        weekNumbers={true}
        weekText="第"
        height="100%"
        eventTimeFormat={{
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        }}
      />
    </CalendarWrapper>
  );
};

export default CalendarView;