// src/components/DocumentsManageTab.jsx
import React, { useEffect, useState } from 'react';

const DocumentsManageTab = ({ refreshSystemInfo }) => {
	const [loading, setLoading] = useState(false);
	const [successMessage, setSuccessMessage] = useState('');
	const [errorMessage, setErrorMessage] = useState('');
	const [documents, setDocuments] = useState([]);
	const [noDocuments, setNoDocuments] = useState(false);
	const [isRebuilding, setIsRebuilding] = useState(false);

	const fetchDocuments = async () => {
		setLoading(true);
		setNoDocuments(false);
		try {
			const response = await fetch('/api/documents');
			const data = await response.json();

			if (data.status === 'success') {
				setDocuments(data.documents || []);
				setNoDocuments(data.documents.length === 0);
			} else {
				alert(`Failed to get document list: ${data.message}`);
			}
		} catch (error) {
			console.error('Failed to get document list:', error);
			alert('Failed to get document list, please check network connection');
		} finally {
			setLoading(false);
		}
	};

	const rebuildKnowledgeBase = async () => {
		setIsRebuilding(true);
		setSuccessMessage('');
		setErrorMessage('');

		try {
			const response = await fetch('/api/rebuild', {
				method: 'POST',
			});
			const data = await response.json();

			if (data.status === 'success') {
				setSuccessMessage(data.message);
				fetchDocuments(); // Refresh documents after rebuilding
				refreshSystemInfo(); // Refresh system info after rebuilding
				
				// 触发自定义事件通知其他组件
				window.dispatchEvent(new CustomEvent('knowledgeBaseRebuilt'));
			} else {
				setErrorMessage(data.message);
			}
		} catch (error) {
			console.error('Failed to rebuild knowledge base:', error);
			setErrorMessage('Failed to rebuild knowledge base, please check network connection.');
		} finally {
			setIsRebuilding(false);
		}
	};

	useEffect(() => {
		fetchDocuments(); // Fetch documents on mount
	}, []);

	return (
		<div className="flex flex-col min-h-screen pb-16"> {/* 给下方添加一些填充，以确保内容不覆盖固定按钮 */}
			<div className="flex-grow"> {/* 使这里的内容可扩展 */}
				<h3>Knowledge Base Documents</h3>

				{isRebuilding && (
					<div className="loading flex items-center my-4">
						<div className="spinner border-4 border-gray-300 rounded-full border-t-blue-600 animate-spin w-8 h-8"></div>
						<p>Rebuilding knowledge base...</p>
					</div>
				)}

				{successMessage && <div className="message-box success bg-green-100 text-green-700 p-2 rounded mt-2">{successMessage}</div>}
				{errorMessage && <div className="message-box error bg-red-100 text-red-700 p-2 rounded mt-2">{errorMessage}</div>}

				{loading && (
					<div className="loading flex items-center my-4">
						<div className="spinner border-4 border-gray-300 rounded-full border-t-blue-600 animate-spin w-8 h-8"></div>
						<p>Loading documents...</p>
					</div>
				)}

				<div id="documents-list" className="documents-list">
					{documents.map((doc, index) => (
						<div key={index} className="document-item flex items-center p-3 border border-gray-300 rounded my-1">
							<div className="document-icon mr-2 text-gray-600">📄</div>
							<div className="text-black">{doc}</div>
						</div>
					))}
					{noDocuments && (
						<div className="no-documents text-gray-600 italic mt-2">There are no documents in the knowledge base.</div>
					)}
				</div>
			</div>

			{/* 创建一个容器用于按钮，并使其固定位置 */}
			<div className="fixed bottom-0 left-1/2 transform -translate-x-1/2 mb-4"> {/* 使用 fixed 定位和 translate 使按钮居中 */}
				<button
					id="refresh-rebuild-btn"
					className="p-2 bg-blue-600 text-white rounded"
					onClick={isRebuilding ? null : rebuildKnowledgeBase}
					disabled={loading || isRebuilding}
				>
					{isRebuilding ? 'Rebuilding...' : 'Rebuild Knowledge Base & Refresh Documents'}
				</button>
			</div>
		</div>
	);
};

export default DocumentsManageTab;