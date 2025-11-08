// React Component (IntegratedTab.jsx) - 整合查询和文档管理功能
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
	
	// 对话历史状态
	const [chatHistory, setChatHistory] = useState([]);
	// 当前问题（用于显示正在进行的对话）
	const [currentQuestion, setCurrentQuestion] = useState('');

	// 文档管理相关状态
	const [documents, setDocuments] = useState([]);
	const [vectorizedDocuments, setVectorizedDocuments] = useState([]);
	const [documentsLoading, setDocumentsLoading] = useState(false);
	const [successMessage, setSuccessMessage] = useState('');
	const [errorMessage, setErrorMessage] = useState('');
	const [messageSource, setMessageSource] = useState(''); // 'upload' 或 'rebuild'
	const [isRebuilding, setIsRebuilding] = useState(false);
	const [showSourcesModal, setShowSourcesModal] = useState(false);
	const [uploading, setUploading] = useState(false);
	const fileInputRef = useRef(null);

	// 自动清除成功消息
	useEffect(() => {
		if (successMessage) {
			const timer = setTimeout(() => {
				setSuccessMessage('');
			}, 3000); // 3秒后自动消失

			return () => clearTimeout(timer);
		}
	}, [successMessage]);

	useEffect(() => {
		// 滚动到 answer-box 底部
		if (results && resultsRef.current) {
			resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
		}
	}, [results]);

	// 获取所有文档列表
	const fetchDocuments = async () => {
		setDocumentsLoading(true);
		try {
			const response = await fetch('/api/documents');
			const data = await response.json();

			if (data.status === 'success') {
				// 去重：确保文档列表中没有重复项
				const uniqueDocuments = Array.from(new Set(data.documents || []));
				setDocuments(uniqueDocuments);
			} else {
				console.error('Failed to get document list:', data.message);
			}
		} catch (error) {
			console.error('Failed to get document list:', error);
		} finally {
			setDocumentsLoading(false);
		}
	};

	// 获取已向量化的文档列表
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
		setMessageSource('upload');

		try {
			const formData = new FormData();
			formData.append('file', file);

			const response = await fetch('/api/documents/upload', {
				method: 'POST',
				body: formData,
			});

			const data = await response.json();

			if (data.status === 'success') {
				setSuccessMessage(data.message);
				setMessageSource('upload');
				fetchDocuments(); // 刷新文档列表
				// 重置文件输入
				if (fileInputRef.current) {
					fileInputRef.current.value = '';
				}
			} else {
				setErrorMessage(data.message);
				setMessageSource('upload');
			}
		} catch (error) {
			console.error('Failed to upload file:', error);
			setErrorMessage('Failed to upload file, please check network connection.');
			setMessageSource('upload');
		} finally {
			setUploading(false);
		}
	};

	// 重建知识库
	const rebuildKnowledgeBase = async () => {
		setIsRebuilding(true);
		setSuccessMessage('');
		setErrorMessage('');
		setMessageSource('rebuild');

		try {
			const response = await fetch('/api/rebuild', {
				method: 'POST',
			});
			const data = await response.json();

			// 无论成功还是失败，都刷新文档列表，确保显示与后端一致
			fetchDocuments();
			fetchVectorizedDocuments();
			
			if (data.status === 'success') {
				setSuccessMessage(data.message);
				setMessageSource('rebuild');
				refreshSystemInfo();
				
				// 触发自定义事件通知其他组件
				window.dispatchEvent(new CustomEvent('knowledgeBaseRebuilt'));
			} else {
				setErrorMessage(data.message);
				setMessageSource('rebuild');
			}
		} catch (error) {
			console.error('Failed to rebuild knowledge base:', error);
			setErrorMessage('Failed to rebuild knowledge base, please check network connection.');
			setMessageSource('rebuild');
			// 即使出错也刷新文档列表
			fetchDocuments();
			fetchVectorizedDocuments();
		} finally {
			setIsRebuilding(false);
		}
	};

	// 发送查询
	const sendStreamQuery = async () => {
		if (!queryInput) return;

		const currentQuery = queryInput;
		setCurrentQuestion(currentQuery); // 保存当前问题
		setLoading(true);
		setResults('');
		setSources([]);
		setQueryError('');

		// 用于累积完整的回答
		let fullAnswer = '';

		try {
			const response = await fetch('/api/query/stream', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ 
					query: currentQuery,
					chat_history: chatHistory
				}),
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

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
									setResults(prevResults => prevResults + event.token);
									break;
								case 'sources':
									setSources(event.sources);
									break;
								case 'error':
									setQueryError(event.error);
									setLoading(false);
									break;
								case 'end':
									// 查询完成，保存到对话历史
									if (fullAnswer.trim()) {
										setChatHistory(prevHistory => {
											const newHistory = [...prevHistory, {
												question: currentQuery,
												answer: fullAnswer
											}];
											// 限制历史记录数量（最多保留10轮对话）
											return newHistory.slice(-10);
										});
									}
									setQueryInput('');
									setCurrentQuestion(''); // 清除当前问题
									setLoading(false);
									break;
								default:
									console.warn('Unknown event type:', event.type);
							}
						} catch (parseError) {
							console.error('Failed to parse JSON:', jsonData, parseError);
							setQueryError(`Error parsing server response: ${parseError.message}`);
						}
					}
				}
			}
		} catch (networkError) {
			console.error('Network error:', networkError);
			setQueryError(`Network error: ${networkError.message}`);
		} finally {
			setLoading(false);
		}
	};

	// 组件挂载时获取数据
	useEffect(() => {
		if (isInitialized) {
			fetchDocuments();
			fetchVectorizedDocuments();
		}
	}, [isInitialized]);

	// 监听重建事件
	useEffect(() => {
		if (!isInitialized) return;

		const handleRebuildComplete = () => {
			fetchVectorizedDocuments();
		};

		window.addEventListener('knowledgeBaseRebuilt', handleRebuildComplete);
		return () => {
			window.removeEventListener('knowledgeBaseRebuilt', handleRebuildComplete);
		};
	}, [isInitialized]);

	return (
		<div className="h-screen bg-gray-50 flex flex-col">
			{/* 顶部状态栏 - 紧凑设计 */}
			<div className="flex-shrink-0 border-b border-gray-200 bg-white px-12 py-3">
				<div className="w-full">
					<div className="flex items-center justify-between">
						<div className="flex items-center space-x-3">
							<div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
								<span className="text-white text-base font-bold">AI</span>
							</div>
							<div>
								<h1 className="text-lg font-semibold text-gray-900">RAGenius</h1>
							</div>
						</div>
						<div className="flex items-center space-x-3 text-sm text-gray-500">
							<span>{vectorizedDocuments.length}/{documents.length} 文档</span>
							{chatHistory.length > 0 && (
								<button
									onClick={() => {
										setChatHistory([]);
										setResults('');
										setSources([]);
										setCurrentQuestion('');
										setQueryError('');
									}}
									className="w-10 h-10 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors flex items-center justify-center cursor-pointer"
									title="清除对话历史"
								>
									<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</button>
							)}
							{/* 文件管理按钮 */}
							<button
								onClick={() => {
									document.getElementById('sidebar').classList.remove('translate-x-full');
								}}
								className="w-10 h-10 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors flex items-center justify-center cursor-pointer"
								title="打开文档管理"
							>
								<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
							</button>
							{/* 重建按钮 */}
							<button
								onClick={rebuildKnowledgeBase}
								disabled={isRebuilding}
								className="w-10 h-10 bg-blue-600 hover:bg-blue-700 text-white rounded-full transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shadow-sm hover:shadow-md"
								title={isRebuilding ? '重建中' : '重建知识库'}
							>
								{isRebuilding ? (
									<div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
								) : (
									<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
									</svg>
								)}
							</button>
						</div>
					</div>
				</div>
			</div>

			{/* 消息区域 - 使用calc确保准确的高度计算 */}
			<div className="flex-1 overflow-y-auto" style={{height: 'calc(100vh - 120px)'}}>
				<div className="max-w-5xl mx-auto px-6 py-4 space-y-4">
						{/* 欢迎消息 - 只在没有任何对话时显示 */}
						{chatHistory.length === 0 && !currentQuestion && !results && !loading && (
							<div className="text-center py-8">
								<div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-3">
									<span className="text-white text-lg">🤖</span>
								</div>
								<h2 className="text-lg font-semibold text-gray-900 mb-2">你好！我是 RAGenius</h2>
								<p className="text-sm text-gray-500 mb-4">我可以帮你查询知识库中的信息</p>
								
								{/* 知识库状态 - 简化版 */}
								{vectorizedDocuments.length > 0 ? (
									<div className="inline-flex items-center px-3 py-1 bg-green-50 text-green-700 text-xs rounded-full">
										<div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
										已加载 {vectorizedDocuments.length} 个文档
									</div>
								) : (
									<div className="inline-flex items-center px-3 py-1 bg-yellow-50 text-yellow-700 text-xs rounded-full">
										<div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
										知识库未初始化
									</div>
								)}
							</div>
						)}

						{/* 显示所有历史对话 */}
						{chatHistory.map((turn, index) => (
							<div key={index} className="space-y-3">
								{/* 用户问题 */}
								<div className="flex items-start space-x-2 justify-end">
									<div className="flex-1 max-w-[80%] bg-blue-50 rounded-lg px-4 py-3 shadow-sm border border-blue-200">
										<p className="text-gray-900 leading-relaxed">{turn.question}</p>
									</div>
									<div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
										<span className="text-white text-xs font-bold">你</span>
									</div>
								</div>

								{/* AI回答 */}
								<div className="flex items-start space-x-2">
									<div className="w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
										<span className="text-white text-xs font-bold">AI</span>
									</div>
									<div className="flex-1 bg-white rounded-lg px-3 py-3 shadow-sm border border-gray-200">
										<div className="text-gray-800 leading-relaxed">
											<ReactMarkdown 
												remarkPlugins={[remarkGfm]}
												components={{
													p: ({children}) => <p className="mb-3 leading-relaxed text-gray-800">{children}</p>,
													h1: ({children}) => <h1 className="text-xl font-bold mb-4 text-gray-900 border-b border-gray-200 pb-2">{children}</h1>,
													h2: ({children}) => <h2 className="text-lg font-semibold mb-3 text-gray-900">{children}</h2>,
													h3: ({children}) => <h3 className="text-base font-medium mb-2 text-gray-900">{children}</h3>,
													h4: ({children}) => <h4 className="text-sm font-medium mb-2 text-gray-700">{children}</h4>,
													ul: ({children}) => <ul className="list-disc list-inside mb-3 space-y-1 text-gray-800 ml-4">{children}</ul>,
													ol: ({children}) => <ol className="list-decimal list-inside mb-3 space-y-1 text-gray-800 ml-4">{children}</ol>,
													li: ({children}) => <li className="text-gray-800 leading-relaxed">{children}</li>,
													blockquote: ({children}) => (
														<blockquote className="border-l-4 border-blue-400 pl-4 py-2 mb-3 bg-blue-50 italic text-gray-700 rounded-r">
															{children}
														</blockquote>
													),
													strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
													em: ({children}) => <em className="italic text-gray-700">{children}</em>,
													hr: () => <hr className="my-4 border-gray-300" />,
													table: ({children}) => (
														<div className="overflow-x-auto mb-3">
															<table className="w-full border-collapse border border-gray-300 text-sm">
																{children}
															</table>
														</div>
													),
													thead: ({children}) => <thead className="bg-gray-100">{children}</thead>,
													tbody: ({children}) => <tbody>{children}</tbody>,
													tr: ({children}) => <tr className="border-b border-gray-200">{children}</tr>,
													th: ({children}) => <th className="border border-gray-300 px-3 py-2 text-left font-semibold text-gray-900">{children}</th>,
													td: ({children}) => <td className="border border-gray-300 px-3 py-2 text-gray-800">{children}</td>,
													pre: ({children}) => (
														<pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto mb-3 border border-gray-200">
															{children}
														</pre>
													),
												}}
											>
												{turn.answer}
											</ReactMarkdown>
										</div>
									</div>
								</div>
							</div>
						))}

						{/* 查询错误 */}
						{queryError && (
							<div className="flex items-start space-x-2">
								<div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0">
									<span className="text-white text-xs">⚠</span>
								</div>
								<div className="flex-1 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
									<p className="text-red-700 text-sm">{queryError}</p>
								</div>
							</div>
						)}

						{/* 当前正在进行的对话 */}
						{currentQuestion && (
							<div className="space-y-3">
								{/* 用户问题 */}
								<div className="flex items-start space-x-2 justify-end">
									<div className="flex-1 max-w-[80%] bg-blue-50 rounded-lg px-4 py-3 shadow-sm border border-blue-200">
										<p className="text-gray-900 leading-relaxed">{currentQuestion}</p>
									</div>
									<div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
										<span className="text-white text-xs font-bold">你</span>
									</div>
								</div>

								{/* 加载状态 - 显示在用户问题下方 */}
								{loading && !results && (
									<div className="flex items-start space-x-2">
										<div className="w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
											<span className="text-white text-xs font-bold">AI</span>
										</div>
										<div className="flex-1 bg-white rounded-lg px-3 py-2 shadow-sm border border-gray-200">
											<div className="flex items-center space-x-1">
												<div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
												<div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
												<div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
											</div>
										</div>
									</div>
								)}

								{/* AI回复（正在生成） */}
								{results && (
									<>
										<div className="flex items-start space-x-2">
											<div className="w-6 h-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
												<span className="text-white text-xs font-bold">AI</span>
											</div>
											<div className="flex-1 bg-white rounded-lg px-3 py-3 shadow-sm border border-gray-200" ref={resultsRef}>
												<div className="text-gray-800 leading-relaxed">
													{results && (
														<ReactMarkdown 
															remarkPlugins={[remarkGfm]}
															components={{
																p: ({children}) => <p className="mb-3 leading-relaxed text-gray-800">{children}</p>,
																h1: ({children}) => <h1 className="text-xl font-bold mb-4 text-gray-900 border-b border-gray-200 pb-2">{children}</h1>,
																h2: ({children}) => <h2 className="text-lg font-semibold mb-3 text-gray-900">{children}</h2>,
																h3: ({children}) => <h3 className="text-base font-medium mb-2 text-gray-900">{children}</h3>,
																h4: ({children}) => <h4 className="text-sm font-medium mb-2 text-gray-700">{children}</h4>,
																ul: ({children}) => <ul className="list-disc list-inside mb-3 space-y-1 text-gray-800 ml-4">{children}</ul>,
																ol: ({children}) => <ol className="list-decimal list-inside mb-3 space-y-1 text-gray-800 ml-4">{children}</ol>,
																li: ({children}) => <li className="text-gray-800 leading-relaxed">{children}</li>,
																blockquote: ({children}) => (
																	<blockquote className="border-l-4 border-blue-400 pl-4 py-2 mb-3 bg-blue-50 italic text-gray-700 rounded-r">
																		{children}
																	</blockquote>
																),
																strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
																em: ({children}) => <em className="italic text-gray-700">{children}</em>,
																hr: () => <hr className="my-4 border-gray-300" />,
																table: ({children}) => (
																	<div className="overflow-x-auto mb-3">
																		<table className="w-full border-collapse border border-gray-300 text-sm">
																			{children}
																		</table>
																	</div>
																),
																thead: ({children}) => <thead className="bg-gray-100">{children}</thead>,
																tbody: ({children}) => <tbody>{children}</tbody>,
																tr: ({children}) => <tr className="border-b border-gray-200">{children}</tr>,
																th: ({children}) => <th className="border border-gray-300 px-3 py-2 text-left font-semibold text-gray-900">{children}</th>,
																td: ({children}) => <td className="border border-gray-300 px-3 py-2 text-gray-800">{children}</td>,
																pre: ({children}) => (
																	<pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto mb-3 border border-gray-200">
																		{children}
																	</pre>
																),
																// 注意：不重写code组件，让CSS处理
															}}
														>
															{results}
														</ReactMarkdown>
													)}
												</div>
											</div>
										</div>

										{/* 参考来源按钮 - 只在内容生成完成后显示 */}
										{sources.length > 0 && !loading && (
											<div className="ml-8 mt-3">
												<button
													onClick={() => setShowSourcesModal(true)}
													className="inline-flex items-center px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-medium rounded-full border border-blue-200 transition-colors duration-200"
												>
													<svg className="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
													</svg>
													参考来源 ({sources.length})
												</button>
											</div>
										)}
									</>
								)}
							</div>
						)}

					{/* 浮动通知消息 */}
					{(successMessage || errorMessage) && (
						<div className="fixed top-4 left-1/2 z-50 notification-enter">
							<div className={`px-4 py-2 rounded-lg shadow-lg text-sm flex items-center space-x-2 ${
								successMessage 
									? 'bg-green-500 text-white' 
									: 'bg-red-500 text-white'
							}`}>
								<span className="text-lg">
									{successMessage ? '✅' : '❌'}
								</span>
								<span>{successMessage || errorMessage}</span>
							</div>
						</div>
					)}
				</div>
			</div>

			{/* 固定在底部的输入区域 - ChatGPT风格 */}
			<div className="flex-shrink-0 border-t border-gray-200 bg-white px-6 py-3">
				<div className="max-w-5xl mx-auto">
					<div className="relative">
						<input
							type="text"
							placeholder="发送消息给 RAGenius..."
							value={queryInput}
							onChange={(e) => setQueryInput(e.target.value)}
							onKeyPress={(e) => e.key === 'Enter' && !loading && queryInput.trim() && sendStreamQuery()}
							className="w-full pl-4 pr-12 py-3 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
							disabled={loading}
						/>
						<button
							onClick={sendStreamQuery}
							disabled={loading || !queryInput.trim()}
							className="absolute right-2 top-1/2 transform -translate-y-1/2 w-8 h-8 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 rounded-md flex items-center justify-center transition-colors"
						>
							{loading ? (
								<div className="w-4 h-4 border-2 border-gray-600 border-t-transparent rounded-full animate-spin"></div>
							) : (
								<svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
								</svg>
							)}
						</button>
					</div>
				</div>
			</div>

			{/* 参考来源弹窗 */}
			{showSourcesModal && (
				<div className="fixed inset-0 backdrop-blur-sm bg-white bg-opacity-20 flex items-center justify-center z-50 p-4" onClick={() => setShowSourcesModal(false)}>
					<div className="bg-white rounded-lg shadow-2xl ring-1 ring-black ring-opacity-5 max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
						{/* 弹窗头部 */}
						<div className="flex items-center justify-between p-4 border-b border-gray-200">
							<h3 className="text-lg font-semibold text-gray-900 flex items-center">
								<svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
								参考来源 ({sources.length})
							</h3>
							<button
								onClick={() => setShowSourcesModal(false)}
								className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
							>
								<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>
						
						{/* 弹窗内容 */}
						<div className="flex-1 p-4 overflow-y-auto min-h-0">
							<div className="space-y-4">
								{sources.map((source, index) => (
									<div key={index} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
										<div className="flex items-start space-x-3">
											<div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
												<span className="text-blue-600 text-sm font-medium">{index + 1}</span>
											</div>
											<div className="flex-1 min-w-0">
												<h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
													<svg className="w-4 h-4 mr-1.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
													</svg>
													{source.source}
												</h4>
												<div className="text-sm text-gray-700 leading-relaxed bg-white p-4 rounded border max-h-60 overflow-y-auto">
													<div className="whitespace-pre-wrap break-words">
														{source.content}
													</div>
												</div>
											</div>
										</div>
									</div>
								))}
							</div>
						</div>
						
						{/* 弹窗底部 */}
						<div className="flex-shrink-0 flex justify-end p-4 border-t border-gray-200 bg-gray-50">
							<button
								onClick={() => setShowSourcesModal(false)}
								className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium rounded-lg transition-colors"
							>
								关闭
							</button>
						</div>
					</div>
				</div>
			)}

			{/* 侧边栏 - 文档管理 */}
			<div className="fixed right-0 top-0 h-full w-80 bg-white border-l border-gray-200 transform translate-x-full transition-transform duration-300 ease-in-out z-50" id="sidebar">
				<div className="p-6 flex flex-col h-full">
					<div className="flex items-center justify-between mb-6">
						<h3 className="text-lg font-semibold text-gray-900">文档管理</h3>
						<button className="text-gray-400 hover:text-gray-600" onClick={() => {
							document.getElementById('sidebar').classList.add('translate-x-full');
						}}>
							<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>

					{/* 上传文件按钮 */}
					<div className="mb-4">
						<input
							type="file"
							ref={fileInputRef}
							onChange={handleFileUpload}
							accept=".pdf,.txt,.md,.csv,.docx,.doc"
							className="hidden"
							id="file-upload-input"
							disabled={uploading}
						/>
						<button
							onClick={() => fileInputRef.current?.click()}
							disabled={uploading}
							className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
						>
							{uploading ? (
								<>
									<div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
									<span>上传中...</span>
								</>
							) : (
								<>
									<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
									</svg>
									<span>上传文件</span>
								</>
							)}
						</button>
					</div>

					{/* 消息提示 - 只显示重建知识库的消息 */}
					{(successMessage || errorMessage) && messageSource === 'rebuild' && (
						<div className={`mb-4 px-3 py-2 rounded-lg text-sm ${
							successMessage ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
						}`}>
							{successMessage || errorMessage}
						</div>
					)}

					{/* 文档列表 */}
					<div className="flex-1 space-y-2 overflow-y-auto">
						{documents.length > 0 ? (
							// 去重：确保每个文件只显示一次
							Array.from(new Set(documents)).map((doc) => {
								const isVectorized = vectorizedDocuments.includes(doc);
								return (
									<div key={doc} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50">
										<div className="flex items-center space-x-3">
											<div className="text-lg">
												{doc.endsWith('.pdf') ? '📕' : 
												 doc.endsWith('.txt') ? '📄' : 
												 doc.endsWith('.md') ? '📝' : 
												 doc.endsWith('.csv') ? '📊' : 
												 doc.endsWith('.docx') || doc.endsWith('.doc') ? '📘' : '📄'}
											</div>
											<div className="flex-1 min-w-0">
												<p className="text-sm font-medium text-gray-900 truncate">{doc}</p>
											</div>
										</div>
										<div className={`w-2 h-2 rounded-full ${isVectorized ? 'bg-green-500' : 'bg-gray-300'}`}></div>
									</div>
								);
							})
						) : (
							<div className="text-center py-8 text-gray-500">
								<div className="text-3xl mb-2">📭</div>
								<p className="text-sm">暂无文档</p>
							</div>
						)}
					</div>
				</div>
			</div>

		</div>
	);
};

export default IntegratedTab;
