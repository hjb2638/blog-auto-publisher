import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createArticle } from '../api/articles';
import type { ArticleMode } from '../types';

export default function ArticleCreatePage() {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [requirements, setRequirements] = useState('');
  const [mode, setMode] = useState<ArticleMode>('manual');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim().length < 10) {
      setError('Topic must be at least 10 characters');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const result = await createArticle({
        topic: topic.trim(),
        requirements: requirements.trim() || undefined,
        mode,
      });
      navigate(`/articles/${result.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create article');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-12 px-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">New Article</h2>
      <form onSubmit={handleSubmit} className="card space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Topic</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., Write a technical blog about LoRA fine-tuning"
            className="input-field"
            disabled={submitting}
            autoFocus
          />
          <p className="text-xs text-gray-400 mt-1">{topic.length}/500 (min 10)</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Additional Requirements <span className="text-gray-400">(optional)</span>
          </label>
          <textarea
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            placeholder="Any specific requirements, style preferences, or key topics to cover..."
            className="input-field h-24 resize-none"
            disabled={submitting}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Mode</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="mode"
                value="manual"
                checked={mode === 'manual'}
                onChange={() => setMode('manual')}
                className="text-blue-600"
              />
              <span className="text-sm text-gray-700">
                <strong>Manual</strong> — Review and approve each step
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="mode"
                value="auto"
                checked={mode === 'auto'}
                onChange={() => setMode('auto')}
                className="text-blue-600"
              />
              <span className="text-sm text-gray-700">
                <strong>Auto</strong> — Skip reviews, publish immediately
              </span>
            </label>
          </div>
        </div>

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <button type="submit" disabled={submitting} className="btn-primary w-full py-3">
          {submitting ? 'Generating Outline...' : 'Generate Outline'}
        </button>
      </form>
    </div>
  );
}
