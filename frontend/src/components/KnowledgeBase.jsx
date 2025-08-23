// src/components/KnowledgeBase.jsx
import React, { useEffect, useRef, useState } from 'react';
import IntegratedTab from './IntegratedTab';
import { FaExclamationTriangle, FaCogs } from 'react-icons/fa';

const KnowledgeBase = () => {
	const [modelInfo, setModelInfo] = useState('Model: Loading...');
	const [isInitialized, setIsInitialized] = useState(false);
	const warningMessageRef = useRef(null);

	useEffect(() => {
		fetchSystemInfo();
	}, []);

	const fetchSystemInfo = async () => {
		try {
			const response = await fetch('/api/info');
			const data = await response.json();
			if (data.status === 'success') {
				setModelInfo(`Model: ${data.model} | Embedding Model: ${data.embedding_model} | Threads: ${data.threads}`);
				setIsInitialized(data.initialized);
				if (warningMessageRef.current) {
					warningMessageRef.current.style.display = data.initialized ? 'none' : 'block';
				}
			}
		} catch (error) {
			console.error('Failed to get system information:', error);
			setModelInfo('System connection failed');
		}
	};

	return (
		<div className="h-screen w-full overflow-hidden">
			{/* 警告消息 - 固定在顶部 */}
			{!isInitialized && (
				<div className="bg-yellow-50 border-b border-yellow-200 px-6 py-3 flex items-center justify-center">
					<div className="flex items-center space-x-2 text-yellow-800">
						<FaExclamationTriangle className="h-4 w-4" />
						<span className="text-sm font-medium">知识库尚未初始化，请先重建知识库</span>
					</div>
				</div>
			)}
			
			{/* 主界面 */}
			<IntegratedTab isInitialized={isInitialized} refreshSystemInfo={fetchSystemInfo} />
		</div>
	);
};

export default KnowledgeBase;