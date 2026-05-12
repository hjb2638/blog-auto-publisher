import { Route, Routes } from 'react-router-dom';
import Layout from './components/layout/Layout';
import WelcomePage from './pages/WelcomePage';
import ArticleCreatePage from './pages/ArticleCreatePage';
import ArticleDetailPage from './pages/ArticleDetailPage';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/new" element={<ArticleCreatePage />} />
        <Route path="/articles/:id" element={<ArticleDetailPage />} />
      </Routes>
    </Layout>
  );
}
