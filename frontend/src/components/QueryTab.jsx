import React, { useState } from 'react';

const QueryTab = ({ isInitialized }) => {
	const [queryInput, setQueryInput] = useState('');
	const [loading, setLoading] = useState(false);
	const [results, setResults] = useState(null);
	const [sources, setSources] = useState([]);

	const sendStreamQuery = async () => {
		if (!queryInput) return;

		setLoading(true);
		setResults(null);
		setSources([]);

		try {
			const response = await fetch(`/api/query/stream?q=${encodeURIComponent(queryInput)}`);
			const reader = response.body.getReader();
			const decoder = new TextDecoder('utf-8');

			let markdownBuffer = '';
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				markdownBuffer += decoder.decode(value, { stream: true });
			}
			setResults(markdownBuffer);
			setSources([]); // Extract sources as necessary
		} catch (error) {
			console.error('Failed to process query:', error);
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
					placeholder="Please enter your question..."
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
					Query
				</button>
			</div>

			{loading && (
				<div className="loading flex flex-col items-center my-4">
					<div className="spinner border-4 border-gray-300 rounded-full border-t-blue-600 animate-spin w-8 h-8"></div>
					<p>Processing query...</p>
				</div>
			)}

			{results && (
				<div className="results my-4">
					<div className="answer-box mb-4">
						<h3>Answer:</h3>
						<div id="answer-content" className="bg-blue-50 p-3 rounded">{results}</div>
					</div>

					<div className="sources-box">
						<h3>Reference Sources:</h3>
						{sources.length > 0 ? (
							sources.map((source, index) => (
								<div key={index} className="source-item p-3 border border-gray-300 rounded my-1">
									<div className="source-title font-medium">{`Source ${index + 1}: ${source.source}`}</div>
									<div className="source-content">{source.content}</div>
								</div>
							))
						) : (
							<div className="text-gray-600 italic">No sources available.</div>
						)}
					</div>
				</div>
			)}


		</div>
	);
};

export default QueryTab;