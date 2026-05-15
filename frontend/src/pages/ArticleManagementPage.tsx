import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useArticlesPaginated } from '../hooks/useArticlesPaginated';
import { useArticleSelection } from '../hooks/useArticleSelection';
import ArticleTable from '../components/articles/ArticleTable';
import ConfirmDialog from '../components/common/ConfirmDialog';
import { batchAction } from '../api/articles';

const SOURCE_TABS = [
  { label: 'All', value: undefined },
  { label: 'Local', value: 'local' },
  { label: 'WordPress', value: 'wordpress' },
] as const;

export default function ArticleManagementPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string | undefined>();
  const [source, setSource] = useState<string | undefined>();
  const [showBatchConfirm, setShowBatchConfirm] = useState(false);
  const [batchActionType, setBatchActionType] = useState<string>('');
  const [batchDeleteWp, setBatchDeleteWp] = useState(true);
  const limit = 20;

  const { data, isLoading } = useArticlesPaginated(page, limit, status, source);
  const { selectedIds, toggle, selectAll, clearSelection, isAllSelected } = useArticleSelection();

  const articles = data?.data || [];
  const meta = data?.meta;
  const totalPages = meta?.pages || 1;
  const allIds = articles.map((a) => a.id);

  const batchMutation = useMutation({
    mutationFn: batchAction,
    onSuccess: () => {
      clearSelection();
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });

  const selectedArticles = articles.filter((a) => selectedIds.has(a.id));
  const selectedCount = selectedIds.size;

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Article Management</h1>
        <button
          onClick={() => navigate('/new')}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
        >
          + New Article
        </button>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        {SOURCE_TABS.map(({ label, value }) => (
          <button
            key={label}
            onClick={() => { setSource(value); setPage(1); }}
            className={`px-3 py-1.5 text-xs font-medium rounded-full ${
              source === value
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <ArticleTable
        articles={articles}
        isLoading={isLoading}
        currentPage={page}
        totalPages={totalPages}
        statusFilter={status}
        selectedIds={selectedIds}
        onToggle={toggle}
        onSelectAll={selectAll}
        isAllSelected={isAllSelected(allIds)}
        onPageChange={setPage}
        onStatusFilter={(s) => { setStatus(s); setPage(1); }}
      />

      {selectedCount > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-40">
          <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
            <span className="text-sm text-gray-600">
              {selectedCount} selected
            </span>
            <div className="flex items-center gap-2">
              {selectedArticles.every((a) => a.status === 'published') && (
                <button
                  onClick={() => {
                    setBatchActionType('unpublish');
                    setShowBatchConfirm(true);
                  }}
                  className="px-3 py-1.5 text-sm text-yellow-700 border border-yellow-300 bg-yellow-50 rounded-md hover:bg-yellow-100"
                >
                  Unpublish Selected
                </button>
              )}
              <button
                onClick={() => {
                  setBatchActionType('cancel');
                  setShowBatchConfirm(true);
                }}
                className="px-3 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel Selected
              </button>
              <button
                onClick={() => {
                  setBatchActionType('delete');
                  setShowBatchConfirm(true);
                }}
                className="px-3 py-1.5 text-sm text-white bg-red-600 rounded-md hover:bg-red-700"
              >
                Delete Selected
              </button>
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={showBatchConfirm}
        title={
          batchActionType === 'delete' ? 'Batch Delete' :
          batchActionType === 'unpublish' ? 'Batch Unpublish' :
          'Batch Cancel'
        }
        message={
          batchActionType === 'delete'
            ? `Delete ${selectedCount} article${selectedCount > 1 ? 's' : ''}?${
                selectedCount <= 5
                  ? '\n\n' + selectedArticles.map((a) => `• ${a.displayTitle}`).join('\n')
                  : ''
              } This action cannot be undone.`
            : batchActionType === 'unpublish'
            ? `Unpublish ${selectedCount} article${selectedCount > 1 ? 's' : ''} from WordPress? The articles will remain in the system as final_approved.`
            : `Cancel ${selectedCount} article${selectedCount > 1 ? 's' : ''}?`
        }
        confirmLabel={
          batchActionType === 'delete' ? 'Delete' :
          batchActionType === 'unpublish' ? 'Unpublish' :
          'Cancel'
        }
        variant={batchActionType === 'delete' ? 'danger' : 'primary'}
        checkbox={
          batchActionType === 'delete'
            ? { label: 'Also delete from WordPress', checked: batchDeleteWp, onChange: setBatchDeleteWp }
            : undefined
        }
        onConfirm={() => {
          setShowBatchConfirm(false);
          batchMutation.mutate({
            ids: Array.from(selectedIds),
            action: batchActionType,
            ...(batchActionType === 'delete' ? { deleteWp: batchDeleteWp } : {}),
          });
        }}
        onCancel={() => setShowBatchConfirm(false)}
      />
    </div>
  );
}
