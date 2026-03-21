import React, { useState, useEffect } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  TextField, 
  Button,
  IconButton,
  Typography,
  Box,
  Paper,
  Tooltip
} from '@mui/material';
import { Close as CloseIcon, Edit as EditIcon } from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import styled from 'styled-components';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

// 假设我们有一个 dailySummary 相关的 redux slice
import { 
  selectDailySummaries, 
  fetchDailySummaries, 
  createDailySummary, 
  updateDailySummary 
} from '@store/slices/dailySummarySlice';

const SummaryPaper = styled(Paper)`
  padding: 16px;
  margin-top: 16px;
  background-color: #f9f9f9;
  border-left: 4px solid #42a5f5;
`;

const SummaryHeader = styled(Box)`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

interface DailySummaryProps {
  date: Date;
}

interface DailySummaryDialogProps {
  open: boolean;
  onClose: () => void;
  date: Date;
  initialValue: string;
  onSave: (content: string) => void;
}

// 每日总结对话框组件
const DailySummaryDialog: React.FC<DailySummaryDialogProps> = ({
  open,
  onClose,
  date,
  initialValue,
  onSave
}) => {
  const [content, setContent] = useState(initialValue);

  useEffect(() => {
    setContent(initialValue);
  }, [initialValue, open]);

  const handleSave = () => {
    onSave(content);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            {format(date, 'yyyy年MM月dd日 EEEE', { locale: zhCN })} 学习总结
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          multiline
          rows={8}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          fullWidth
          variant="outlined"
          placeholder="记录今天的学习收获、遇到的问题和解决方案..."
          margin="normal"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSave} color="primary" variant="contained">
          保存
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// 每日总结组件
const DailySummary: React.FC<DailySummaryProps> = ({ date }) => {
  const dispatch = useDispatch();
  const summaries = useSelector(selectDailySummaries);
  const [dialogOpen, setDialogOpen] = useState(false);
  
  // 日期格式化为 YYYY-MM-DD
  const dateStr = format(date, 'yyyy-MM-dd');
  
  // 查找当前日期的总结
  const currentSummary = summaries.find(summary => summary.date === dateStr);
  
  useEffect(() => {
    // 获取当前日期的总结
    dispatch(fetchDailySummaries(dateStr));
  }, [dateStr, dispatch]);
  
  const handleSave = (content: string) => {
    if (currentSummary) {
      dispatch(updateDailySummary({
        id: currentSummary.id,
        date: dateStr,
        description: content
      }));
    } else {
      dispatch(createDailySummary({
        date: dateStr,
        description: content
      }));
    }
  };
  
  return (
    <>
      {currentSummary ? (
        <SummaryPaper elevation={1}>
          <SummaryHeader>
            <Typography variant="subtitle1" fontWeight={500}>
              今日学习总结
            </Typography>
            <Tooltip title="编辑总结">
              <IconButton size="small" onClick={() => setDialogOpen(true)}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </SummaryHeader>
          <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
            {currentSummary.description || '暂无总结内容'}
          </Typography>
        </SummaryPaper>
      ) : (
        <SummaryPaper elevation={1}>
          <SummaryHeader>
            <Typography variant="subtitle1" fontWeight={500}>
              今日学习总结
            </Typography>
          </SummaryHeader>
          <Box display="flex" justifyContent="center" padding={2}>
            <Button 
              variant="outlined" 
              color="primary" 
              onClick={() => setDialogOpen(true)}
            >
              添加今日总结
            </Button>
          </Box>
        </SummaryPaper>
      )}
      
      <DailySummaryDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        date={date}
        initialValue={currentSummary?.description || ''}
        onSave={handleSave}
      />
    </>
  );
};

export default DailySummary;