import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiGetKnowledgeDocs, apiUploadKnowledge } from '../../api/mock';
import type { KnowledgeDoc } from '../../api/types';

export default function KnowledgeBase() {
  const navigate = useNavigate();
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    apiGetKnowledgeDocs().then(setDocs);
  }, []);

  const handleUpload = async () => {
    setUploading(true);
    const fileName = prompt('请输入文件名（如：主展厅讲解词.txt）：') || '新文档.txt';
    const doc = await apiUploadKnowledge(fileName);
    setDocs((prev) => [doc, ...prev]);
    setUploading(false);

    // Simulate processing -> ready
    setTimeout(() => {
      setDocs((prev) => prev.map((d) => (d.docId === doc.docId ? { ...d, status: 'ready' } : d)));
    }, 3000);
  };

  return (
    <>
      <div className="page">
        <div className="page-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <button
              onClick={() => navigate('/')}
              style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', padding: '4px 6px', borderRadius: 8 }}
            >← 返回</button>
          </div>
          <h1>📚 知识库管理</h1>
          <p className="subtitle">上传景区资料，构建专属知识库</p>
        </div>

        {/* Upload */}
        <div className="upload-area" onClick={handleUpload} style={{ marginTop: 12 }}>
          <div className="upload-icon">📤</div>
          <p><strong>点击上传文档</strong></p>
          <p>支持 TXT、MD、PDF 格式（第一周支持 TXT/MD）</p>
        </div>
        {uploading && <p className="text-secondary" style={{ textAlign: 'center' }}>上传处理中...</p>}

        {/* File List */}
        <div className="card">
          <div className="card-title">📄 已上传文档 ({docs.length})</div>
          {docs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <p>暂无文档，点击上方上传</p>
            </div>
          ) : (
            <ul className="file-list">
              {docs.map((doc) => (
                <li key={doc.docId} className="file-item">
                  <span className="file-icon">{doc.fileType === 'md' ? '📝' : '📃'}</span>
                  <div className="file-name">
                    <span>{doc.fileName}</span>
                    <div className="text-secondary">{doc.uploadAt}</div>
                  </div>
                  <span className={`file-status ${doc.status}`}>
                    {doc.status === 'ready' ? '已就绪' : '处理中'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  );
}
