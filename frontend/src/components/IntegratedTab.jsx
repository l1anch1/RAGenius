// RAGenius - Modern Light Silicon Valley UI
// IntegratedTab.jsx - 聊天界面组件
import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const IntegratedTab = ({ isInitialized, refreshSystemInfo }) => {
	// 查询相关状态
	const [queryInput, setQueryInput] = useState('');
	const [loading, setLoading] = useState(false);
	const [results, setResults] = useState('');
	const [sources, setSources] = useState([]);
	const [queryError, setQueryError] = useState('');
	const resultsRef = useRef(null);
	const messagesEndRef = useRef(null);
	
	// 对话历史状态
	const [chatHistory, setChatHistory] = useState([]);
	const [currentQuestion, setCurrentQuestion] = useState('');

	// 文档管理相关状态
	const [documents, setDocuments] = useState([]);
	const [vectorizedDocuments, setVectorizedDocuments] = useState([]);
	const [documentsLoading, setDocumentsLoading] = useState(false);
	const [successMessage, setSuccessMessage] = useState('');
	const [errorMessage, setErrorMessage] = useState('');
	const [isRebuilding, setIsRebuilding] = useState(false);
	const [showSourcesModal, setShowSourcesModal] = useState(false);
	const [uploading, setUploading] = useState(false);
	const [sidebarOpen, setSidebarOpen] = useState(false);
	const fileInputRef = useRef(null);
	
	// 自动滚动到底部
	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	};

	useEffect(() => {
		scrollToBottom();
	}, [chatHistory, results, currentQuestion]);

	// 自动清除消息
	useEffect(() => {
		if (successMessage || errorMessage) {
			const timer = setTimeout(() => {
				setSuccessMessage('');
				setErrorMessage('');
			}, 4000);
			return () => clearTimeout(timer);
		}
	}, [successMessage, errorMessage]);

	// 获取文档列表
	const fetchDocuments = async () => {
		setDocumentsLoading(true);
		try {
			const response = await fetch('/api/documents');
			const data = await response.json();
			if (data.status === 'success') {
				const uniqueDocuments = Array.from(new Set(data.documents || []));
				setDocuments(uniqueDocuments);
			}
		} catch (error) {
			console.error('Failed to get document list:', error);
		} finally {
			setDocumentsLoading(false);
		}
	};

	// 获取已向量化的文档
	const fetchVectorizedDocuments = async () => {
		try {
			const response = await fetch('/api/documents/vectorized');
			if (response.ok) {
				const data = await response.json();
				setVectorizedDocuments(data.documents || []);
			}
		} catch (error) {
			console.error('Failed to fetch vectorized documents:', error);
		}
	};

	// 上传文件
	const handleFileUpload = async (event) => {
		const file = event.target.files[0];
		if (!file) return;

		setUploading(true);
		setSuccessMessage('');
		setErrorMessage('');

		try {
			const formData = new FormData();
			formData.append('file', file);

			const response = await fetch('/api/documents/upload', {
				method: 'POST',
				body: formData,
			});

			const data = await response.json();

			if (data.status === 'success') {
				setSuccessMessage(`✨ ${file.name} uploaded successfully`);
				fetchDocuments();
				if (fileInputRef.current) {
					fileInputRef.current.value = '';
				}
			} else {
				setErrorMessage(data.message);
			}
		} catch (error) {
			setErrorMessage('Upload failed. Please check your network connection.');
		} finally {
			setUploading(false);
		}
	};

	// 删除文档
	const deleteDocument = async (filename) => {
		if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

		try {
			const response = await fetch('/api/documents/delete', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ filename }),
			});
			const data = await response.json();

			if (data.status === 'success') {
				setSuccessMessage('Document deleted');
				fetchDocuments();
			} else {
				setErrorMessage(data.message);
			}
		} catch (error) {
			setErrorMessage('Delete failed');
		}
	};

	// 清空所有文档
	const clearAllDocuments = async () => {
		if (!confirm('Are you sure you want to clear all documents?')) return;

		try {
			const response = await fetch('/api/documents/clear', { method: 'POST' });
			const data = await response.json();

			if (data.status === 'success') {
				setSuccessMessage('All documents cleared');
				fetchDocuments();
				fetchVectorizedDocuments();
				refreshSystemInfo();
			} else {
				setErrorMessage(data.message);
			}
		} catch (error) {
			setErrorMessage('Clear failed');
		}
	};

	// 重建知识库
	const rebuildKnowledgeBase = async () => {
		setIsRebuilding(true);
		setSuccessMessage('');
		setErrorMessage('');

		try {
			const response = await fetch('/api/rebuild', { method: 'POST' });
			const data = await response.json();

			fetchDocuments();
			fetchVectorizedDocuments();
			
			if (data.status === 'success') {
				setSuccessMessage('🚀 Knowledge base rebuilt successfully');
				refreshSystemInfo();
				window.dispatchEvent(new CustomEvent('knowledgeBaseRebuilt'));
			} else {
				setErrorMessage(data.message);
			}
		} catch (error) {
			setErrorMessage('Rebuild failed');
			fetchDocuments();
			fetchVectorizedDocuments();
		} finally {
			setIsRebuilding(false);
		}
	};

	// 发送查询
	const sendStreamQuery = async () => {
		if (!queryInput.trim()) return;

		const currentQuery = queryInput;
		setCurrentQuestion(currentQuery);
		setLoading(true);
		setResults('');
		setSources([]);
		setQueryError('');

		let fullAnswer = '';

		try {
			const response = await fetch('/api/query/stream', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ 
					query: currentQuery,
					chat_history: chatHistory
				}),
			});

			if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

			const reader = response.body.getReader();
			const decoder = new TextDecoder('utf-8');
			let partialData = "";

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				partialData += decoder.decode(value);
				let parts = partialData.split('\n\n');
				partialData = parts.pop();

				for (const part of parts) {
					if (!part) continue;

					const dataPrefix = "data: ";
					if (part.startsWith(dataPrefix)) {
						const jsonData = part.substring(dataPrefix.length);
						try {
							const event = JSON.parse(jsonData);

							switch (event.type) {
								case 'token':
									fullAnswer += event.token;
									setResults(prev => prev + event.token);
									break;
								case 'sources':
									setSources(event.sources);
									break;
								case 'error':
									setQueryError(event.error);
									setLoading(false);
									break;
								case 'end':
									if (fullAnswer.trim()) {
										setChatHistory(prev => {
											const newHistory = [...prev, {
												question: currentQuery,
												answer: fullAnswer
											}];
											return newHistory.slice(-10);
										});
									}
									setQueryInput('');
									setCurrentQuestion('');
									setLoading(false);
									break;
							}
						} catch (parseError) {
							console.error('Failed to parse JSON:', parseError);
						}
					}
				}
			}
		} catch (networkError) {
			setQueryError(`Network error: ${networkError.message}`);
		} finally {
			setLoading(false);
		}
	};

	// 组件挂载 - 总是获取文档列表
	useEffect(() => {
		fetchDocuments();
		fetchVectorizedDocuments();
	}, []);

	// isInitialized 变化时刷新
	useEffect(() => {
		if (isInitialized) {
			fetchDocuments();
			fetchVectorizedDocuments();
		}
	}, [isInitialized]);

	// Markdown 组件配置
	const markdownComponents = {
		p: ({ children }) => <p className="mb-3 leading-relaxed text-[--text-secondary]">{children}</p>,
		h1: ({ children }) => <h1 className="text-xl font-bold mb-4 mt-6 text-[--text-primary]">{children}</h1>,
		h2: ({ children }) => <h2 className="text-lg font-semibold mb-3 mt-5 text-[--text-primary]">{children}</h2>,
		h3: ({ children }) => <h3 className="text-base font-medium mb-2 mt-4 text-[--text-primary]">{children}</h3>,
		ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1 ml-2">{children}</ul>,
		ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1 ml-2">{children}</ol>,
		li: ({ children }) => <li className="text-[--text-secondary] leading-relaxed">{children}</li>,
		blockquote: ({ children }) => (
			<blockquote className="border-l-4 border-[--accent-mid] pl-4 py-2 my-3 bg-[--soft-purple] rounded-r-xl italic text-[--text-secondary]">
				{children}
			</blockquote>
		),
		strong: ({ children }) => <strong className="font-bold text-[--text-primary]">{children}</strong>,
		hr: () => <hr className="my-6 border-[--border-color]" />,
		table: ({ children }) => (
			<div className="overflow-x-auto my-4">
				<table className="w-full border-collapse text-sm border border-[--border-color] rounded-xl overflow-hidden">{children}</table>
			</div>
		),
		thead: ({ children }) => <thead className="bg-[--bg-tertiary]">{children}</thead>,
		th: ({ children }) => <th className="border border-[--border-color] px-4 py-3 text-left font-semibold text-[--text-primary]">{children}</th>,
		td: ({ children }) => <td className="border border-[--border-color] px-4 py-3 text-[--text-secondary]">{children}</td>,
		pre: ({ children }) => (
			<pre className="bg-[--bg-tertiary] border border-[--border-color] rounded-xl p-4 overflow-x-auto my-4 text-sm">
				{children}
			</pre>
		),
	};

	// 获取文档图标
	const getDocIcon = (filename) => {
		if (filename.endsWith('.pdf')) return '📕';
		if (filename.endsWith('.txt')) return '📄';
		if (filename.endsWith('.md')) return '📝';
		if (filename.endsWith('.csv')) return '📊';
		if (filename.endsWith('.docx') || filename.endsWith('.doc')) return '📘';
		return '📄';
	};

	return (
		<div className="h-full flex flex-col relative">
			{/* 背景效果 */}
			<div className="bg-pattern">
				<div className="grid-overlay"></div>
				<div className="floating-shapes"></div>
			</div>

			{/* Toast 通知 */}
			{(successMessage || errorMessage) && (
				<div className={`toast ${successMessage ? 'toast-success' : 'toast-error'}`}>
					<span>{successMessage || errorMessage}</span>
				</div>
			)}

			{/* 顶部导航栏 */}
			<header className="relative z-20 flex-shrink-0 px-6 py-4 bg-[--bg-primary]/95 backdrop-blur-sm">
				<div className="max-w-5xl mx-auto flex items-center justify-between">
					{/* Logo */}
					<div className="flex items-center gap-4">
						<div className="logo-container">
							<div className="logo-glow"></div>
							<div className="relative w-12 h-12 rounded-[14px] bg-gradient-to-br from-[--accent-start] via-[--accent-mid] to-[--accent-end] flex items-center justify-center shadow-lg">
								<svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
								</svg>
							</div>
							</div>
							<div>
							<h1 className="text-xl font-bold gradient-text">RAGenius</h1>
							<p className="text-xs text-[--text-tertiary] font-medium">AI-Powered Knowledge</p>
							</div>
						</div>

					{/* 右侧操作区 */}
					<div className="flex items-center gap-2">
						{/* 清除对话 - 有对话时才显示 */}
						{chatHistory.length > 0 && (
							<button
								onClick={() => {
									setChatHistory([]);
									setResults('');
									setSources([]);
									setCurrentQuestion('');
									setQueryError('');
								}}
								className="btn-ghost text-sm flex items-center gap-2 px-3 py-2"
							>
								<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
								<span className="hidden sm:inline">Clear</span>
							</button>
						)}

						{/* 分隔线 */}
						{chatHistory.length > 0 && (
							<div className="h-6 w-px bg-[--border-color] mx-1"></div>
						)}

						{/* 文档管理按钮 - 带文字和数量 */}
						<button
							onClick={() => setSidebarOpen(true)}
							className="btn-secondary text-sm flex items-center gap-2 px-4 py-2"
						>
							<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
							</svg>
							<span>Docs</span>
							{vectorizedDocuments.length > 0 && (
								<span className="bg-[--accent-mid] text-white text-xs font-bold px-1.5 py-0.5 rounded-full min-w-[20px] text-center">
									{vectorizedDocuments.length}
								</span>
							)}
						</button>

						{/* 重建按钮 - 主要操作，突出显示 */}
						<button
							onClick={rebuildKnowledgeBase}
							disabled={isRebuilding || documents.length === 0}
							className="btn-primary text-sm flex items-center gap-2 px-4 py-2"
							title={documents.length === 0 ? 'Upload documents first' : 'Build knowledge base from documents'}
						>
							{isRebuilding ? (
								<>
									<div className="spinner w-4 h-4"></div>
									<span className="hidden sm:inline">Building...</span>
								</>
							) : (
								<>
									<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
									</svg>
									<span>Build</span>
								</>
							)}
						</button>
					</div>
				</div>
			</header>

			{/* 消息区域 - flex-1 让它填充剩余空间，overflow-y-auto 启用滚动 */}
			<main className="relative z-10 flex-1 overflow-y-auto px-6 py-6">
				<div className="max-w-4xl mx-auto space-y-6">
					{/* 欢迎界面 */}
						{chatHistory.length === 0 && !currentQuestion && !results && !loading && (
						<div className="flex flex-col items-center justify-center min-h-[60vh] text-center animate-fade-in-up">
							<div className="welcome-icon mb-8 animate-float">
								<svg className="w-12 h-12 text-white relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
								</svg>
								</div>
							<h2 className="text-4xl font-extrabold mb-4 gradient-text">Hi, I'm RAGenius</h2>
							<p className="text-[--text-secondary] text-lg mb-10 max-w-lg leading-relaxed">
								Intelligent Q&A powered by your document knowledge base
							</p>
							
							{/* 功能提示卡片 */}
							<div className="flex flex-wrap justify-center gap-5 max-w-3xl">
								{[
									{ icon: '📄', title: 'Upload Documents', desc: 'Supports PDF, TXT, MD and more', color: 'purple' },
									{ icon: '🔍', title: 'Smart Retrieval', desc: 'Semantic + keyword hybrid search', color: 'blue' },
									{ icon: '💬', title: 'Chat Q&A', desc: 'Multi-turn dialogue with context', color: 'pink' }
								].map((item, i) => (
									<div 
										key={i} 
										className="feature-card flex-1 min-w-[200px] max-w-[240px]"
										style={{ animationDelay: `${i * 0.1}s` }}
									>
										<div className="feature-card-icon">{item.icon}</div>
										<h3 className="font-bold text-[--text-primary] mb-2 text-lg">{item.title}</h3>
										<p className="text-sm text-[--text-tertiary] leading-relaxed">{item.desc}</p>
									</div>
								))}
									</div>
							</div>
						)}

					{/* 对话历史 */}
						{chatHistory.map((turn, index) => (
						<div key={index} className="space-y-5 animate-fade-in-up" style={{ animationDelay: `${index * 0.1}s` }}>
							{/* 用户消息 */}
							<div className="flex justify-end gap-3">
								<div className="message-user">
									<p className="leading-relaxed">{turn.question}</p>
									</div>
								<div className="avatar-user">U</div>
								</div>

							{/* AI 回复 */}
							<div className="flex gap-3">
								<div className="avatar-ai">
									<svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
									</svg>
									</div>
								<div className="message-ai flex-1">
									<div className="markdown-content">
										<ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
												{turn.answer}
											</ReactMarkdown>
										</div>
									</div>
								</div>
							</div>
						))}

					{/* 当前对话 */}
						{currentQuestion && (
						<div className="space-y-5 animate-fade-in-up">
								{/* 用户问题 */}
							<div className="flex justify-end gap-3">
								<div className="message-user">
									<p className="leading-relaxed">{currentQuestion}</p>
									</div>
								<div className="avatar-user">U</div>
								</div>

							{/* AI 回复 */}
							<div className="flex gap-3">
								<div className="avatar-ai">
									<svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
									</svg>
										</div>
								<div className="message-ai flex-1">
									{loading && !results ? (
										<div className="loading-dots py-2">
											<div className="loading-dot"></div>
											<div className="loading-dot"></div>
											<div className="loading-dot"></div>
											</div>
									) : (
										<div className="markdown-content" ref={resultsRef}>
											<ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
															{results}
														</ReactMarkdown>
										</div>
													)}
											</div>
										</div>

							{/* 来源按钮 */}
										{sources.length > 0 && !loading && (
								<div className="ml-12">
												<button
													onClick={() => setShowSourcesModal(true)}
										className="badge badge-info cursor-pointer hover:opacity-80 transition-opacity"
												>
										<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
														<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
													</svg>
										<span>View {sources.length} sources</span>
												</button>
											</div>
								)}
							</div>
						)}

					{/* 错误提示 */}
					{queryError && (
						<div className="flex gap-3 animate-fade-in">
							<div className="w-9 h-9 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0">
								<svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
							</div>
							<div className="glass-card px-5 py-3 border-red-200 bg-red-50">
								<p className="text-red-600 text-sm font-medium">{queryError}</p>
							</div>
						</div>
					)}

					<div ref={messagesEndRef} />
				</div>
			</main>

			{/* 输入区域 */}
			<footer className="relative z-20 flex-shrink-0 px-6 py-4 bg-[--bg-primary]/95 backdrop-blur-sm">
				<div className="max-w-4xl mx-auto">
					<div className="glass-card-strong p-3">
						<div className="relative flex items-center">
						<input
							type="text"
								placeholder="Ask RAGenius anything..."
							value={queryInput}
							onChange={(e) => setQueryInput(e.target.value)}
							onKeyPress={(e) => e.key === 'Enter' && !loading && queryInput.trim() && sendStreamQuery()}
								className="input-glow"
							disabled={loading}
						/>
						<button
							onClick={sendStreamQuery}
							disabled={loading || !queryInput.trim()}
								className="absolute right-3 w-12 h-12 rounded-[14px] bg-gradient-to-r from-[--accent-start] to-[--accent-mid] flex items-center justify-center transition-all hover:shadow-lg hover:shadow-[--accent-mid]/30 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none disabled:hover:scale-100"
						>
							{loading ? (
									<div className="spinner"></div>
							) : (
									<svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
								</svg>
							)}
						</button>
					</div>
				</div>
				<p className="text-center text-xs text-[--text-tertiary] mt-4 font-medium">
					RAGenius generates answers from your documents. Please verify important information.
				</p>
			</div>
			</footer>

			{/* 侧边栏背景遮罩 */}
			<div 
				className={`sidebar-backdrop ${sidebarOpen ? 'open' : ''}`}
				onClick={() => setSidebarOpen(false)}
			/>

			{/* 侧边栏 */}
			<aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
				<div className="flex flex-col h-full p-7">
					{/* 侧边栏头部 */}
					<div className="flex items-center justify-between mb-7">
						<h2 className="text-xl font-bold text-[--text-primary]">Documents</h2>
							<button
							onClick={() => setSidebarOpen(false)}
							className="btn-icon w-10 h-10"
						>
							<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>

					{/* 上传区域 */}
					<div className="space-y-3 mb-7">
						<input
							type="file"
							ref={fileInputRef}
							onChange={handleFileUpload}
							accept=".pdf,.txt,.md,.csv,.docx,.doc"
							className="hidden"
							id="file-upload"
							disabled={uploading}
						/>
						<button
							onClick={() => fileInputRef.current?.click()}
							disabled={uploading}
							className="btn-primary w-full flex items-center justify-center gap-3"
						>
							{uploading ? (
								<>
									<div className="spinner"></div>
									<span>Uploading...</span>
								</>
							) : (
								<>
									<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
									</svg>
									<span>Upload Document</span>
								</>
							)}
						</button>

						{(documents.length > 0 || vectorizedDocuments.length > 0) && (
							<button
								onClick={clearAllDocuments}
								className="btn-ghost w-full flex items-center justify-center gap-2 text-red-500 border-red-200 hover:bg-red-50 hover:border-red-300"
							>
								<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
								<span>Clear All</span>
							</button>
						)}
					</div>

					{/* 文档列表 */}
					<div className="flex-1 overflow-y-auto custom-scrollbar -mx-2">
						{(() => {
							// 合并 documents 和 vectorizedDocuments（去重）
							const allDocs = Array.from(new Set([...documents, ...vectorizedDocuments]));
							
							if (allDocs.length > 0) {
								return (
									<div className="space-y-2">
										{allDocs.map((doc) => {
								const isVectorized = vectorizedDocuments.includes(doc);
											const isInMemory = documents.includes(doc);
											const isOrphanedVector = isVectorized && !isInMemory; // 只有向量数据，没有原始文件
											
								return (
												<div key={doc} className="doc-item group">
													<div className="doc-icon">{getDocIcon(doc)}</div>
											<div className="flex-1 min-w-0">
														<p className="text-sm font-semibold text-[--text-primary] truncate">{doc}</p>
														{isOrphanedVector && (
															<p className="text-xs text-[--text-tertiary]">Restored from cache</p>
														)}
											</div>
													<div className={`doc-status ${isVectorized ? 'active' : 'inactive'}`}></div>
													{isInMemory ? (
														<button
															onClick={() => deleteDocument(doc)}
															className="opacity-0 group-hover:opacity-100 p-2 text-[--text-tertiary] hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
														>
															<svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
																<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
															</svg>
														</button>
													) : (
														<span className="text-xs text-[--text-tertiary] px-2">🔒</span>
													)}
										</div>
											);
										})}
									</div>
								);
							} else {
								return (
									<div className="flex flex-col items-center justify-center h-full text-center py-16">
										<div className="text-5xl mb-4 opacity-60">📂</div>
										<p className="text-[--text-secondary] font-medium">No documents yet</p>
										<p className="text-[--text-tertiary] text-sm mt-1">Click above to upload</p>
							</div>
								);
							}
						})()}
					</div>

					{/* 底部提示 */}
					<div className="mt-5 pt-5 border-t border-[--border-color]">
						<p className="text-xs text-[--text-tertiary] text-center font-medium">
							Supports PDF, TXT, MD, CSV, DOCX
						</p>
				</div>
			</div>
			</aside>

			{/* 来源弹窗 */}
			{showSourcesModal && (
				<div className="modal-backdrop" onClick={() => setShowSourcesModal(false)}>
					<div className="modal-content" onClick={(e) => e.stopPropagation()}>
						{/* 弹窗头部 */}
						<div className="flex items-center justify-between p-6 border-b border-[--border-color]">
							<h3 className="text-xl font-bold text-[--text-primary] flex items-center gap-3">
								<div className="w-10 h-10 rounded-xl bg-[--soft-purple] flex items-center justify-center">
									<svg className="w-5 h-5 text-[--accent-mid]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
									</svg>
								</div>
								Sources ({sources.length})
							</h3>
							<button
								onClick={() => setShowSourcesModal(false)}
								className="btn-icon w-10 h-10"
							>
								<svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>

						{/* 弹窗内容 */}
						<div className="p-6 overflow-y-auto max-h-[55vh] custom-scrollbar space-y-4">
							{sources.map((source, index) => (
								<div key={index} className="glass-card p-5">
									<div className="flex items-start gap-4">
										<div className="w-10 h-10 rounded-xl bg-[--soft-purple] flex items-center justify-center flex-shrink-0">
											<span className="text-[--accent-mid] text-sm font-bold">{index + 1}</span>
										</div>
										<div className="flex-1 min-w-0">
											<h4 className="text-sm font-bold text-[--text-primary] mb-3 flex items-center gap-2">
												{getDocIcon(source.source)}
												{source.source}
											</h4>
											<div className="text-sm text-[--text-secondary] leading-relaxed bg-[--bg-tertiary] p-4 rounded-xl border border-[--border-color] max-h-44 overflow-y-auto custom-scrollbar">
												{source.content}
											</div>
										</div>
									</div>
								</div>
							))}
			</div>

						{/* 弹窗底部 */}
						<div className="p-6 border-t border-[--border-color] flex justify-end">
							<button
								onClick={() => setShowSourcesModal(false)}
								className="btn-primary"
							>
								<span>Close</span>
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default IntegratedTab;
