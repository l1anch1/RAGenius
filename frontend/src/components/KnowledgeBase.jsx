// src/components/KnowledgeBase.jsx
import React, { useEffect, useRef, useState } from 'react';
import QueryTab from './QueryTab';
import KnowledgeBaseTab from './DocumentsManageTab';
import { FaSearch, FaExclamationTriangle, FaFile } from 'react-icons/fa';

const KnowledgeBase = () => {
	const [currentTab, setCurrentTab] = useState('query');
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

	const handleTabChange = (tab) => {
		setCurrentTab(tab);
	};

	return (
		<div className="rounded-lg bg-white min-h-screen w-screen p-5 max-w-full overflow-x-auto box-border">
			<header className="bg-blue-100 text-blue-600 p-6 rounded-lg shadow-lg mb-6">
				<h1 className="text-4xl font-semibold">Knowledge Base System</h1>
				<div className="opacity-90 text-m mt-2" id="model-info">
					{modelInfo}
				</div>
			</header>

			<div className="flex border-b border-gray-300 rounded-lg overflow-hidden gap-6">
				<button onClick={() => handleTabChange('query')} className={`tab-btn flex-1 p-3 text-lg font-medium transition-all duration-300 ${currentTab === 'query' ? 'bg-white text-blue-600 border-b-2 border-blue-600 shadow' : 'text-gray-600 hover:bg-blue-100'}`}>
					<div className="flex items-center justify-center">
						<FaSearch className={`mr-2 h-6 w-6 ${currentTab === 'query' ? 'text-blue-600' : 'text-gray-600'}`} />
						Query Knowledge Base
					</div>
				</button>
				<button onClick={() => handleTabChange('knowledgeBase')} className={`tab-btn flex-1 p-3 text-lg font-medium transition-all duration-300 ${currentTab === 'knowledgeBase' ? 'bg-white text-blue-600 border-b-2 border-blue-600 shadow' : 'text-gray-600 hover:bg-blue-100'}`}>
					<div className="flex items-center justify-center">
						<FaFile className={`mr-2 h-6 w-6 ${currentTab === 'knowledgeBase' ? 'text-blue-600' : 'text-gray-600'}`} />
						Documents Management
					</div>
				</button>
			</div>

			<div className="tab-content mt-4 bg-white p-6 shadow-lg">
				<div
					id="warning-message"
					ref={warningMessageRef}
					className={`not-initialized-warning ${isInitialized ? 'hidden' : 'block'} bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-3 rounded`}
				>
					<FaExclamationTriangle className="h-6 w-6 inline-block mr-2" />
					Warning: The knowledge base is not initialized. Please rebuild it first.
				</div>

				<div className={`tab-pane ${currentTab === 'query' ? 'active' : 'hidden'}`}>
					<QueryTab isInitialized={isInitialized} />
				</div>
				<div className={`tab-pane ${currentTab === 'knowledgeBase' ? 'active' : 'hidden'}`}>
					<KnowledgeBaseTab refreshSystemInfo={fetchSystemInfo} />
				</div>
			</div>
		</div>
	);
};

export default KnowledgeBase;