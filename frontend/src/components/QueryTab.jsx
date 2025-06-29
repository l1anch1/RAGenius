// React Component (QueryTab.jsx)
import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

const QueryTab = ({ isInitialized }) => {
	const [queryInput, setQueryInput] = useState('');
	const [loading, setLoading] = useState(false);
	const [results, setResults] = useState('');
	const [sources, setSources] = useState([]);
	const [error, setError] = useState('');  // 用于显示错误信息
	const resultsRef = useRef(null); // 用于跟踪结果，以便正确附加新token

	useEffect(() => {
		// 滚动到 answer-box 底部
		if (results && resultsRef.current) {
			resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
		}
	}, [results]);

	const sendStreamQuery = async () => {
		if (!queryInput) return;

		setLoading(true);
		setResults(''); // Reset results to an empty string
		setSources([]);
		setError('');

		try {
			const response = await fetch('/api/query/stream', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ query: queryInput }),
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder('utf-8');

			let partialData = ""; // 用于存储不完整的 JSON 数据

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				partialData += decoder.decode(value);

				// 处理可能包含多个 event 的数据
				let parts = partialData.split('\n\n');
				partialData = parts.pop(); // 最后一个可能是不完整的 event

				for (const part of parts) {
					if (!part) continue;

					const dataPrefix = "data: ";
					if (part.startsWith(dataPrefix)) {
						const jsonData = part.substring(dataPrefix.length);
						try {
							const event = JSON.parse(jsonData);

							switch (event.type) {
								case 'token':
									setResults(prevResults => prevResults + event.token);
									break;
								case 'sources':
									setSources(event.sources);
									break;
								case 'error':
									setError(event.error); // 显示错误信息
									break;
								case 'end':
									// 流结束，无需操作
									break;
								default:
									console.warn('Unknown event type:', event.type);
							}
						} catch (parseError) {
							console.error('Failed to parse JSON:', jsonData, parseError);
							setError(`Error parsing server response: ${parseError.message}`);
						}
					} else {
						console.warn('Unexpected data format:', part);
					}
				}
			}

		} catch (networkError) {
			console.error('Network error:', networkError);
			setError(`Network error: ${networkError.message}`); // 显示网络错误信息
		} finally {
			setLoading(false);
		}
	};

	return (
		<div>
			<div className="flex mb-4 mt-2">
				<input
					type="text"
					id="query-input"
					placeholder="请输入你的问题..."
					className="flex-1 p-2 border border-gray-300 rounded-l"
					value={queryInput}
					onChange={(e) => setQueryInput(e.target.value)}
				/>
				<button
					id="query-btn"
					className="p-2 bg-blue-600 text-white rounded-r shadow disabled:bg-gray-300"
					onClick={sendStreamQuery}
					disabled={loading || !queryInput}
				>
					查询
				</button>
			</div>

			{loading && (
				<div className="loading flex flex-col items-center my-4">
					<div className="spinner border-4 border-gray-300 rounded-full border-t-blue-600 animate-spin w-8 h-8"></div>
					<p>处理查询中...</p>
				</div>
			)}

			{error && (
				<div className="error my-4 text-red-500">
					<p>错误：{error}</p>
				</div>
			)}

			{results && (
				<div className="results my-4">
					<div className="answer-box mb-4">
						<h3>答案：</h3>
						<div id="answer-content" className="bg-blue-50 p-3 rounded" ref={resultsRef}>
							<ReactMarkdown>{results}</ReactMarkdown>
						</div>
					</div>

					<div className="sources-box">
						<h3>参考来源：</h3>
						{sources.length > 0 ? (
							sources.map((source, index) => (
								<div key={index} className="source-item p-3 border border-gray-300 rounded my-1">
									<div className="source-title font-medium">{`来源 ${index + 1}: ${source.source}`}</div>
									<div className="source-content">{source.content}</div>
								</div>
							))
						) : (
							<div className="text-gray-600 italic">没有可用的来源。</div>
						)}
					</div>
				</div>
			)}
		</div>
	);
};

export default QueryTab;