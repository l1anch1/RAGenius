// RAGenius - Modern Silicon Valley UI
// KnowledgeBase.jsx - 知识库主组件
import React, { useEffect, useState } from 'react';
import IntegratedTab from './IntegratedTab';

const KnowledgeBase = () => {
	const [modelInfo, setModelInfo] = useState('Model: Loading...');
	const [isInitialized, setIsInitialized] = useState(false);

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
			}
		} catch (error) {
			console.error('Failed to get system information:', error);
			setModelInfo('System connection failed');
		}
	};

	return (
		<div className="h-screen w-full overflow-hidden bg-[--bg-primary]">
			<IntegratedTab isInitialized={isInitialized} refreshSystemInfo={fetchSystemInfo} />
		</div>
	);
};

export default KnowledgeBase;
