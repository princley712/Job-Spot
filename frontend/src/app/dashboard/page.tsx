'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { JobModal } from '@/components/job-modal';
import { useTabFocus } from '@/hooks/use-tab-focus';
import { ExternalLink, Building2, MapPin, Target, Sparkles, FileText, CheckCircle2, XCircle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { ResumeUpload } from '@/components/resume-upload';

interface Job {
  id: string; // This is the Application ID
  title: string;
  company: string;
  location: string;
  salary?: string;
  url: string;
  matchScore: number;
  tags: string[];
  skillOverlap?: {
    matched_skills: string[];
    missing_skills: string[];
  };
}

export default function DashboardPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [pendingJob, setPendingJob] = useState<Job | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchJobs = useCallback(async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null;
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Fetch pending applications from the correct backend endpoint
      const res = await fetch('http://localhost:8000/api/v1/applications/?status_filter=pending', {
        headers,
      });

      if (res.ok) {
        const data = await res.json();
        // Map ApplicationOut to Job interface
        const mappedJobs: Job[] = data.map((app: any) => ({
          id: app.id,
          title: app.job.title,
          company: app.job.company,
          location: app.job.location || 'Remote',
          url: app.job.apply_url,
          matchScore: Math.round(app.match_score || 0),
          tags: [], // Backend doesn't provide tags yet
          skillOverlap: app.skill_overlap,
        }));
        setJobs(mappedJobs);
      } else if (res.status === 401) {
        router.push('/login');
        return;
      } else {
        console.error("Failed to fetch applications:", res.statusText);
      }
    } catch (error) {
      console.error("Network error fetching jobs:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleReturnToTab = useCallback(() => {
    if (pendingJob && !isModalOpen) {
      setIsModalOpen(true);
    }
  }, [pendingJob, isModalOpen]);

  useTabFocus(handleReturnToTab, !!pendingJob);

  const handleJobClick = (job: Job) => {
    setPendingJob(job);
    window.open(job.url, '_blank', 'noopener,noreferrer');
  };

  const handleStatusUpdate = async (status: 'APPLIED' | 'PENDING' | 'NOT_INTERESTED') => {
    if (!pendingJob) return;

    // Optimistically update UI
    if (status !== 'PENDING') {
      setJobs((prev) => prev.filter((j) => j.id !== pendingJob.id));
    }
    
    setIsModalOpen(false);
    const appId = pendingJob.id;
    setPendingJob(null);

    // Fire API call to update application status
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null;
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      if (status === 'APPLIED') {
        await fetch(`http://localhost:8000/api/v1/applications/${appId}/status`, {
          method: 'PATCH',
          headers,
          body: JSON.stringify({ status: 'applied' }),
        });
      } else if (status === 'NOT_INTERESTED') {
        await fetch(`http://localhost:8000/api/v1/applications/${appId}`, {
          method: 'DELETE',
          headers,
        });
      }
    } catch (error) {
      console.error("Failed to update application status:", error);
      // Rollback optimistic update if needed
      fetchJobs();
    }
  };

  return (
    <div className="min-h-screen bg-[#fafafa] dark:bg-slate-950 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 md:py-20">
        
        {/* Header Section */}
        <header className="mb-10 flex flex-col gap-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-sm font-medium w-fit mb-2 border border-indigo-100 dark:border-indigo-500/20">
            <Sparkles className="w-4 h-4" />
            Daily Matches Updated
          </div>
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
            Your recommended roles
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-lg">
            We've found {jobs.length} roles that strongly match your background.
          </p>
        </header>

        {/* Job List */}
        <div className="flex flex-col gap-4">
          {isLoading ? (
            // Loading Skeletons
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 flex items-center gap-4">
                <Skeleton className="w-12 h-12 rounded-xl" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-5 w-1/3" />
                  <Skeleton className="h-4 w-1/4" />
                </div>
                <Skeleton className="h-10 w-28 rounded-lg" />
              </div>
            ))
          ) : jobs.length > 0 ? (
            jobs.map((job) => (
              <div 
                key={job.id}
                onClick={() => handleJobClick(job)}
                className="group relative flex flex-col sm:flex-row sm:items-center gap-5 p-5 md:p-6 glass rounded-2xl border border-slate-200/60 dark:border-slate-800 hover:border-indigo-200 dark:hover:border-indigo-500/30 transition-all duration-200 cursor-pointer hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:hover:shadow-[0_8px_30px_rgb(0,0,0,0.2)]"
              >
                {/* Company Initial Badge (Fallback for Logo) */}
                <div className="hidden sm:flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 text-slate-500 dark:text-slate-400 font-semibold text-lg">
                  {job.company.charAt(0)}
                </div>

                {/* Job Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      {job.title}
                    </h3>
                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${
                      job.matchScore >= 80 ? 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 border-green-200 dark:border-green-500/20' : 
                      job.matchScore >= 50 ? 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/20' : 
                      'bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/20'
                    }`}>
                      <Target className="w-3.5 h-3.5" />
                      ATS Match: {job.matchScore}%
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap items-center text-sm text-slate-500 dark:text-slate-400 gap-x-4 gap-y-2 mt-2">
                    <span className="flex items-center gap-1.5"><Building2 className="w-4 h-4" /> {job.company}</span>
                    <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4" /> {job.location}</span>
                    {job.salary && <span className="font-medium text-slate-600 dark:text-slate-300">{job.salary}</span>}
                  </div>
                  
                  {/* Skills/Tags */}
                  {job.skillOverlap && (
                    <div className="mt-4 flex flex-col gap-2 border-t border-slate-100 dark:border-slate-800/60 pt-3">
                      {job.skillOverlap.matched_skills && job.skillOverlap.matched_skills.length > 0 && (
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3 text-green-500" /> Matched
                          </span>
                          {job.skillOverlap.matched_skills.map(skill => (
                            <span key={skill} className="px-2 py-0.5 rounded text-xs font-medium bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 border border-green-100 dark:border-green-500/20">
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}
                      
                      {job.skillOverlap.missing_skills && job.skillOverlap.missing_skills.length > 0 && (
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1">
                            <XCircle className="w-3 h-3 text-red-500" /> Missing
                          </span>
                          {job.skillOverlap.missing_skills.map(skill => (
                            <span key={skill} className="px-2 py-0.5 rounded text-xs font-medium bg-red-50 dark:bg-red-500/10 text-red-700 dark:text-red-400 border border-red-100 dark:border-red-500/20">
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Action CTA */}
                <div className="mt-4 sm:mt-0 shrink-0">
                  <div className="inline-flex items-center justify-center gap-2 h-10 px-5 rounded-xl bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-sm font-medium transition-all active:scale-95 sm:opacity-0 sm:-translate-x-2 sm:group-hover:opacity-100 sm:group-hover:translate-x-0 duration-200">
                    Apply
                    <ExternalLink className="w-4 h-4 opacity-70" />
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="flex flex-col items-center justify-center py-8 w-full">
              <ResumeUpload 
                onUploadSuccess={() => {
                  setIsLoading(true);
                  // Polling could be added here, but for now we just fetch after a short delay
                  setTimeout(fetchJobs, 2000);
                }} 
              />
            </div>
          )}
        </div>

        <JobModal
          isOpen={isModalOpen}
          jobTitle={pendingJob?.title || ''}
          companyName={pendingJob?.company || ''}
          onAction={handleStatusUpdate}
        />
      </main>
    </div>
  );
}
