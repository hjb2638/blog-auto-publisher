import { useNavigate } from 'react-router-dom';

export default function WelcomePage() {
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center max-w-md">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Blog Publisher</h2>
        <p className="text-gray-600 mb-8">
          AI-powered blog writing assistant. Describe your topic, and let the LLM generate
          outlines, write content, find images, and publish to your WordPress site.
        </p>
        <button onClick={() => navigate('/new')} className="btn-primary text-lg px-8 py-3">
          Create Your First Article
        </button>
      </div>
    </div>
  );
}
