import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useArticle } from '../hooks/useArticle';
import {
  useApproveOutline, useApproveContent, useApproveImageKeywords, useApproveFinal,
  usePublishArticle, useRegenerateArticle, useDeleteArticle, useStepBack,
  useUpdateWpArticle,
} from '../hooks/useArticleMutations';
import StatusStepper from '../components/common/StatusStepper';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorDisplay from '../components/common/ErrorDisplay';
import ConfirmDialog from '../components/common/ConfirmDialog';
import OutlineReview from '../components/articles/OutlineReview';
import ContentReview from '../components/articles/ContentReview';
import ImageKeywordReview from '../components/articles/ImageKeywordReview';
import ImageReview from '../components/articles/ImageReview';
import FinalReview from '../components/articles/FinalReview';
import ContentRenderer from '../components/articles/ContentRenderer';
import GenerationProgress from '../components/articles/GenerationProgress';
import StreamingContent from '../components/articles/StreamingContent';
import TokenUsageCard from '../components/articles/TokenUsageCard';
import type { Article } from '../types';

function getElapsed(startedAt: string): number {
  return (Date.now() - new Date(startedAt).getTime()) / 1000;
}

function getSectionNames(article: Article): Record<string, string> {
  const sections = article.content?.sections || article.outline?.sections || [];
  const names: Record<string, string> = {};
  for (const s of sections) {
    names[s.slug] = s.heading;
  }
  return names;
}

export default function ArticleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useArticle(id);
  const queryClient = useQueryClient();
  const [showDelete, setShowDelete] = useState(false);
  const [awaitingStream, setAwaitingStream] = useState(false);

  const article: Article | undefined = data?.data;
  const status = article?.status;

  const approveOutline = useApproveOutline(id);
  const approveContent = useApproveContent(id);
  const approveImageKeywords = useApproveImageKeywords(id);
  const approveFinal = useApproveFinal(id);
  const publishArticle = usePublishArticle(id);
  const regenerateArticle = useRegenerateArticle(id);
  const deleteArticle = useDeleteArticle(id);
  const stepBack = useStepBack(id);
  const updateWp = useUpdateWpArticle(id);

  const [showEditor, setShowEditor] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [deleteWp, setDeleteWp] = useState(true);

  const [, setTick] = useState(0);

  const handleStepBack = () => {
    if (id) stepBack.mutate();
  };

  const handleEdit = () => {
    if (!article) return;
    setEditTitle(article.outline?.title || article.topic);
    setEditContent(article.fullHtml || '');
    setShowEditor(true);
  };

  const handleUnpublish = () => {
    updateWp.mutate({ status: 'draft' });
  };

  const handleUpdateWp = () => {
    updateWp.mutate({ title: editTitle, content: editContent });
    setShowEditor(false);
  };

  useEffect(() => {
    if (!status || !['outline_generating', 'content_generating', 'image_keywords_generating', 'image_searching'].includes(status)) return;
    const timer = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(timer);
  }, [status]);

  useEffect(() => {
    if (status && status !== 'outline_approved') {
      setAwaitingStream(false);
    }
  }, [status]);

  if (isLoading) return <LoadingSpinner message="Loading article..." />;
  if (isError || !article) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">{(error as Error)?.message || 'Article not found'}</p>
        <button onClick={() => navigate('/')} className="mt-4 text-blue-600 text-sm hover:underline">
          Back to Home
        </button>
      </div>
    );
  }

  const isGenerating = ['outline_generating', 'content_generating', 'image_keywords_generating', 'image_searching'].includes(status || '');
  const elapsed = getElapsed(article.createdAt);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{article.topic}</h1>
          <p className="text-sm text-gray-400 mt-1">
            Mode: {article.mode === 'auto' ? 'Auto-Publish' : 'Manual'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {status === 'failed' && (
            <button
              onClick={() => regenerateArticle.mutate('outline')}
              disabled={regenerateArticle.isPending}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              Retry Outline
            </button>
          )}
          {status === 'published' && article.wpPostId && (
            <>
              {article.wpPostUrl && (
                <a
                  href={article.wpPostUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700"
                >
                  View Live
                </a>
              )}
              <button onClick={handleEdit}
                      className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-md">
                Edit
              </button>
              <button onClick={handleUnpublish} disabled={updateWp.isPending}
                      className="px-4 py-2 text-sm text-yellow-600 hover:bg-yellow-50 rounded-md disabled:opacity-50">
                Unpublish
              </button>
              <button onClick={() => setShowDelete(true)}
                      className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md">
                Delete
              </button>
            </>
          )}
          {status !== 'published' && status !== 'publishing' && (
            <button
              onClick={() => setShowDelete(true)}
              className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      <StatusStepper status={status!} mode={article.mode} />

      {article.errorMessage && status !== 'failed' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
          {article.errorMessage}
        </div>
      )}

      {status === 'published' && (
        <>
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
            <div className="text-green-600 text-lg">Published!</div>
            {article.wpPostUrl && (
              <a
                href={article.wpPostUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-block text-blue-600 text-sm hover:underline break-all"
              >
                {article.wpPostUrl}
              </a>
            )}
            {article.fullHtml && (
              <div className="mt-6 text-left">
                <ContentRenderer html={article.fullHtml} />
              </div>
            )}
          </div>

          {showEditor && (
            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-6 mt-6 space-y-4">
              <h3 className="text-sm font-semibold text-gray-900">Edit Published Article</h3>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Title</label>
                <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)}
                       className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Content (HTML)</label>
                <textarea value={editContent} onChange={(e) => setEditContent(e.target.value)} rows={20}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono" />
              </div>
              <div className="flex items-center gap-2">
                <button onClick={handleUpdateWp} disabled={updateWp.isPending}
                        className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md disabled:opacity-50">
                  Save to WordPress
                </button>
                <button onClick={() => setShowEditor(false)}
                        className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-md">
                  Cancel
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {(status === 'content_generating' || (status === 'outline_approved' && awaitingStream)) && (
        <StreamingContent
          articleId={article.id}
          totalSections={article.outline?.sections?.length || article.content?.sections?.length || 0}
          onTokenUpdate={(perStage) => {
            queryClient.setQueryData(['article', id], (old: any) => {
              if (!old?.data) return old;
              return {
                ...old,
                data: {
                  ...old.data,
                  tokenUsage: { ...old.data.tokenUsage, ...perStage },
                },
              };
            });
          }}
        />
      )}

      {['content_approved', 'image_keywords_generating'].includes(status || '') && (
        <div className="bg-white border border-gray-200/80 rounded-2xl shadow-sm p-6 text-center">
          <LoadingSpinner message="Preparing next stage..." />
        </div>
      )}

      {isGenerating && status !== 'content_generating' && article.progress && (
        <GenerationProgress
          progress={article.progress}
          elapsedSeconds={elapsed}
        />
      )}

      {status === 'outline_ready' && article.outline && (
        <OutlineReview
          outline={article.outline}
          topic={article.topic}
          isAuto={article.mode === 'auto'}
          onApprove={(body) => { setAwaitingStream(true); approveOutline.mutate(body); }}
          onBack={handleStepBack}
          isPending={approveOutline.isPending}
        />
      )}

      {status === 'content_ready' && article.content && (
        <ContentReview
          content={article.content}
          isAuto={article.mode === 'auto'}
          onApprove={(body) => approveContent.mutate(body)}
          onBack={handleStepBack}
          isPending={approveContent.isPending}
        />
      )}

      {status === 'image_keywords_ready' && article.imagePlan && (
        <ImageKeywordReview
          imagePlan={article.imagePlan}
          sectionNames={getSectionNames(article)}
          isAuto={article.mode === 'auto'}
          onApprove={(body) => approveImageKeywords.mutate(body)}
          onBack={handleStepBack}
          isPending={approveImageKeywords.isPending}
        />
      )}

      {status === 'images_ready' && article.images && (
        <ImageReview
          images={article.images}
          sections={article.content?.sections}
          isAuto={article.mode === 'auto'}
          onApprove={(body) => approveFinal.mutate(body)}
          onBack={handleStepBack}
          isPending={approveFinal.isPending}
        />
      )}

      {status === 'final_approved' && (
        <FinalReview
          article={article}
          isPending={publishArticle.isPending}
          onPublish={(body) => publishArticle.mutate(body)}
          onBack={handleStepBack}
        />
      )}

      {article.tokenUsage && Object.keys(article.tokenUsage).length > 0 && (
        <div className="mt-6">
          <TokenUsageCard tokenUsage={article.tokenUsage} />
        </div>
      )}

      {status === 'failed' && (
        <ErrorDisplay
          message={article.errorMessage || 'An unknown error occurred'}
          errorStage={article.errorMessage ? undefined : 'generation'}
          onRetry={() => regenerateArticle.mutate('outline')}
        />
      )}

      <ConfirmDialog
        open={showDelete}
        title="Delete Article"
        message="Are you sure you want to delete this article? This action cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        checkbox={article.wpPostId ? { label: 'Also delete from WordPress', checked: deleteWp, onChange: setDeleteWp } : undefined}
        onConfirm={() => {
          setShowDelete(false);
          deleteArticle.mutate(deleteWp);
        }}
        onCancel={() => setShowDelete(false)}
      />
    </div>
  );
}
