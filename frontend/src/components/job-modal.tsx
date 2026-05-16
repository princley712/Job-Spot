import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Check, X, Clock } from 'lucide-react';

interface JobModalProps {
  isOpen: boolean;
  jobTitle: string;
  companyName: string;
  onAction: (status: 'APPLIED' | 'PENDING' | 'NOT_INTERESTED') => void;
}

export function JobModal({ isOpen, jobTitle, companyName, onAction }: JobModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onAction('PENDING')}>
      <DialogContent className="sm:max-w-[420px] p-0 overflow-hidden border-0 shadow-2xl rounded-3xl">
        <div className="bg-slate-50 dark:bg-slate-900/50 p-6 pb-4 border-b border-slate-100 dark:border-slate-800">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
              Just checking in...
            </DialogTitle>
          </DialogHeader>
          <p className="text-slate-500 dark:text-slate-400 mt-2 leading-relaxed">
            Did you end up submitting your application for the <strong className="font-medium text-slate-900 dark:text-white">{jobTitle}</strong> role at <strong className="font-medium text-slate-900 dark:text-white">{companyName}</strong>?
          </p>
        </div>
        
        <div className="p-4 flex flex-col gap-2 bg-white dark:bg-slate-950">
          <Button 
            onClick={() => onAction('APPLIED')} 
            className="w-full justify-start h-12 px-4 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 hover:text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-400 dark:hover:bg-emerald-500/20 border-0 shadow-none transition-colors"
          >
            <div className="bg-emerald-200/50 dark:bg-emerald-500/20 p-1 rounded-full mr-3 flex items-center justify-center">
              <Check className="w-4 h-4" />
            </div>
            Yes, application submitted
          </Button>
          
          <Button 
            onClick={() => onAction('PENDING')} 
            variant="ghost" 
            className="w-full justify-start h-12 px-4 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800/50 transition-colors"
          >
            <div className="bg-slate-200/50 dark:bg-slate-700/50 p-1 rounded-full mr-3 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
            Not yet, keep it pending
          </Button>
          
          <Button 
            onClick={() => onAction('NOT_INTERESTED')} 
            variant="ghost" 
            className="w-full justify-start h-12 px-4 text-slate-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10 dark:hover:text-red-400 transition-colors group"
          >
            <div className="bg-slate-100 dark:bg-slate-800 p-1 rounded-full mr-3 group-hover:bg-red-100 dark:group-hover:bg-red-500/20 flex items-center justify-center">
              <X className="w-4 h-4" />
            </div>
            Actually, I'm not interested
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
