document.addEventListener('DOMContentLoaded', function() {  
    // 获取DOM元素  
    const tabButtons = document.querySelectorAll('.tab-btn');  
    const tabPanes = document.querySelectorAll('.tab-pane');  

    // 系统信息元素  
    const modelInfoElement = document.getElementById('model-info');  
    const warningMessage = document.getElementById('warning-message');  

    // 查询相关元素  
    const queryInput = document.getElementById('query-input');  
    const queryBtn = document.getElementById('query-btn');  
    const queryLoading = document.getElementById('query-loading');  
    const resultsDiv = document.getElementById('results');  
    const answerContent = document.getElementById('answer-content');  
    const sourcesList = document.getElementById('sources-list');  
    const sourcesBox = document.getElementById('sources-box');  

    // 重建知识库相关元素  
    const rebuildBtn = document.getElementById('rebuild-btn');  
    const rebuildLoading = document.getElementById('rebuild-loading');  
    const rebuildSuccess = document.getElementById('rebuild-success');  
    const rebuildError = document.getElementById('rebuild-error');  

    // 文档列表相关元素  
    const refreshDocsBtn = document.getElementById('refresh-docs-btn');  
    const documentsLoading = document.getElementById('documents-loading');  
    const documentsList = document.getElementById('documents-list');  
    const noDocumentsMessage = document.getElementById('no-documents-message');  

    // 系统状态  
    let isInitialized = false;  

    // 切换选项卡  
    tabButtons.forEach(button => {  
        button.addEventListener('click', function() {  
            // 移除所有active类  
            tabButtons.forEach(btn => btn.classList.remove('active'));  
            tabPanes.forEach(pane => pane.classList.remove('active'));  

            // 为当前选项卡添加active类  
            button.classList.add('active');  
            const tabId = button.getAttribute('data-tab');  
            document.getElementById(tabId).classList.add('active');  

            // 如果切换到文档列表标签，自动刷新列表  
            if (tabId === 'documents') {  
                fetchDocuments();  
            }  
        });  
    });  

    // 获取系统信息  
    async function fetchSystemInfo() {  
        try {  
            const response = await fetch('/api/info');  
            const data = await response.json();  

            if (data.status === 'success') {  
                modelInfoElement.textContent = `模型: ${data.model}  |  嵌入模型: ${data.embedding_model}  |  线程数: ${data.threads}`;  
                isInitialized = data.initialized;  

                // 根据初始化状态显示或隐藏警告  
                warningMessage.style.display = isInitialized ? 'none' : 'block';  

                // 根据初始化状态禁用或启用查询按钮  
                queryBtn.disabled = !isInitialized;  
                if (!isInitialized) {  
                    queryBtn.style.backgroundColor = "#a0aec0";  
                } else {  
                    queryBtn.style.backgroundColor = "";  
                }  
            }  
        } catch (error) {  
            console.error('获取系统信息失败:', error);  
            modelInfoElement.textContent = '系统连接失败';  
        }  
    }  

    // 流式查询 - 使用定时批量渲染  
    async function sendStreamQuery() {  
        const query = queryInput.value.trim();  
        if (!query) return;  
    
        // 清空之前的结果并显示加载状态  
        answerContent.innerHTML = '';  
        sourcesList.innerHTML = '';  
        sourcesBox.style.display = 'none';  
        queryLoading.style.display = 'flex';  
        resultsDiv.style.display = 'none';  
    
        // 用于存储源文档信息但不立即显示  
        let sourcesData = [];  
        
        // 用于存储Markdown文本的缓冲区  
        let markdownBuffer = '';  
        
        // 定时渲染相关变量  
        let renderTimer = null;  
        const RENDER_INTERVAL = 300; // 毫秒  
        
        // 添加强制渲染计时器  
        let forceRenderTimer = null;  
        const FORCE_RENDER_INTERVAL = 100; // 强制每2秒渲染一次，避免长时间不渲染  
        
        // 上次渲染的时间戳  
        let lastRenderTime = 0;  
        
        // 渲染函数，避免代码重复  
        function renderMarkdown() {  
            if (markdownBuffer.trim()) {  
                answerContent.innerHTML = marked.parse(markdownBuffer);  
                lastRenderTime = Date.now();  
            }  
        }  
        
        // 设置强制定期渲染计时器  
        function setupForceRenderTimer() {  
            forceRenderTimer = setInterval(() => {  
                // 如果距离上次渲染已超过强制间隔，则强制渲染  
                const now = Date.now();  
                if (now - lastRenderTime >= FORCE_RENDER_INTERVAL) {  
                    renderMarkdown();  
                }  
            }, FORCE_RENDER_INTERVAL);  
        }  
    
        try {  
            // 创建SSE连接  
            const eventSource = new EventSource(`/api/query/stream?q=${encodeURIComponent(query)}`);  
            
            // 首次收到消息时隐藏加载状态并显示结果区域  
            let firstMessageReceived = false;  
            
            // 设置强制渲染定时器  
            setupForceRenderTimer();  
            
            // 记录初始渲染时间  
            lastRenderTime = Date.now();  
    
            eventSource.onmessage = function(event) {  
                // 第一条消息处理  
                if (!firstMessageReceived) {  
                    queryLoading.style.display = 'none';  
                    resultsDiv.style.display = 'block';  
                    firstMessageReceived = true;  
                }  
    
                const data = JSON.parse(event.data);  
    
                if (data.type === 'token') {  
                    // 将token添加到缓冲区  
                    markdownBuffer += data.token;  
                    
                    // 清除先前的渲染定时器  
                    if (renderTimer) clearTimeout(renderTimer);  
                    
                    // 设置新的定时器  
                    renderTimer = setTimeout(() => {  
                        renderMarkdown();  
                    }, RENDER_INTERVAL);  
                    
                    // 记录收到token的时间，可用于调试  
                    // console.log("Token received at:", Date.now());  
                }  
                else if (data.type === 'sources') {  
                    sourcesData = data.sources;  
                }  
                else if (data.type === 'error') {  
                    answerContent.innerHTML = `<div class="error-message">错误: ${data.error}</div>`;  
                    
                    // 清理定时器  
                    if (renderTimer) clearTimeout(renderTimer);  
                    if (forceRenderTimer) clearInterval(forceRenderTimer);  
                    
                    eventSource.close();  
                }  
                else if (data.type === 'end') {  
                    // 流结束时，立即进行最终渲染  
                    renderMarkdown();  
                    
                    // 清理定时器  
                    if (renderTimer) clearTimeout(renderTimer);  
                    if (forceRenderTimer) clearInterval(forceRenderTimer);  
                    
                    // 显示源文档  
                    if (sourcesData.length > 0) {  
                        sourcesList.innerHTML = '';  
                        sourcesData.forEach((source, index) => {  
                            const sourceItem = document.createElement('div');  
                            sourceItem.className = 'source-item';  
    
                            const sourceTitle = document.createElement('div');  
                            sourceTitle.className = 'source-title';  
                            sourceTitle.textContent = `来源 ${index + 1}: ${source.source}`;  
    
                            const sourceContent = document.createElement('div');  
                            sourceContent.className = 'source-content';  
                            sourceContent.textContent = source.content;  
    
                            sourceItem.appendChild(sourceTitle);  
                            sourceItem.appendChild(sourceContent);  
                            sourcesList.appendChild(sourceItem);  
                        });  
    
                        sourcesBox.style.display = 'block';  
                        setTimeout(() => {  
                            sourcesBox.classList.add('show');  
                        }, 10);  
                    }  
    
                    eventSource.close();  
                }  
            };  
    
            eventSource.onerror = function(error) {  
                console.error('EventSource error:', error);  
                queryLoading.style.display = 'none';  
                resultsDiv.style.display = 'block';  
                answerContent.innerHTML += '<div class="error-message">连接错误，请重试</div>';  
                
                // 清理定时器  
                if (renderTimer) clearTimeout(renderTimer);  
                if (forceRenderTimer) clearInterval(forceRenderTimer);  
                
                eventSource.close();  
            };  
    
        } catch (error) {  
            console.error('查询处理失败:', error);  
            queryLoading.style.display = 'none';  
            resultsDiv.style.display = 'block';  
            answerContent.innerHTML = `<div class="error-message">查询处理失败: ${error.message}</div>`;  
            
            // 确保清理定时器  
            if (renderTimer) clearTimeout(renderTimer);  
            if (forceRenderTimer) clearInterval(forceRenderTimer);  
        }  
    }  
    // 重建知识库  
    async function rebuildKnowledgeBase() {  
        // 显示加载，隐藏消息  
        rebuildLoading.style.display = 'flex';  
        rebuildSuccess.style.display = 'none';  
        rebuildError.style.display = 'none';  
        rebuildBtn.disabled = true;  

        try {  
            const response = await fetch('/api/rebuild', {  
                method: 'POST'  
            });  

            const data = await response.json();  

            // 隐藏加载  
            rebuildLoading.style.display = 'none';  
            rebuildBtn.disabled = false;  

            if (data.status === 'success') {  
                rebuildSuccess.textContent = data.message;  
                rebuildSuccess.style.display = 'block';  

                // 重新获取系统信息  
                fetchSystemInfo();  
            } else {  
                rebuildError.textContent = data.message;  
                rebuildError.style.display = 'block';  
            }  
        } catch (error) {  
            rebuildLoading.style.display = 'none';  
            rebuildBtn.disabled = false;  
            console.error('重建知识库失败:', error);  

            rebuildError.textContent = '重建知识库失败，请检查网络连接';  
            rebuildError.style.display = 'block';  
        }  
    }  

    // 获取文档列表  
    async function fetchDocuments() {  
        // 显示加载，隐藏列表和消息  
        documentsLoading.style.display = 'flex';  
        documentsList.innerHTML = '';  
        noDocumentsMessage.style.display = 'none';  

        try {  
            const response = await fetch('/api/documents');  
            const data = await response.json();  

            // 隐藏加载  
            documentsLoading.style.display = 'none';  

            if (data.status === 'success') {  
                if (data.documents && data.documents.length > 0) {  
                    data.documents.forEach(doc => {  
                        const docItem = document.createElement('div');  
                        docItem.className = 'document-item';  

                        // 简单文件图标  
                        const docIcon = document.createElement('span');  
                        docIcon.className = 'document-icon';  
                        docIcon.innerHTML = '📄';  

                        const docName = document.createElement('span');  
                        docName.textContent = doc;  

                        docItem.appendChild(docIcon);  
                        docItem.appendChild(docName);  
                        documentsList.appendChild(docItem);  
                    });  
                } else {  
                    noDocumentsMessage.style.display = 'block';  
                }  
            } else {  
                alert(`获取文档列表失败: ${data.message}`);  
            }  
        } catch (error) {  
            documentsLoading.style.display = 'none';  
            console.error('获取文档列表失败:', error);  
            alert('获取文档列表失败，请检查网络连接');  
        }  
    }  

    // 事件监听器 - 只使用流式查询  
    queryBtn.addEventListener('click', sendStreamQuery);  
    queryInput.addEventListener('keypress', function(e) {  
        if (e.key === 'Enter') sendStreamQuery();  
    });  

    rebuildBtn.addEventListener('click', rebuildKnowledgeBase);  
    refreshDocsBtn.addEventListener('click', fetchDocuments);  

    // 初始化页面  
    fetchSystemInfo();  
});  