// 全局变量
let currentStep = 1;
let uploadedFiles = [];
let availableFilters = {};
let selectedFileId = null;
let selectedFiles = [];
let farmIds = [];
let globalProgressInterval = null;

// API 基础URL
const API_BASE = '/api';

// DOM 元素
const elements = {
    fileInput: document.getElementById('fileInput'),
    selectFileBtn: document.getElementById('selectFileBtn'),
    uploadArea: document.getElementById('uploadArea'),
    uploadProgress: document.getElementById('uploadProgress'),
    fileListSection: document.getElementById('fileListSection'),
    fileList: document.getElementById('fileList'),
    selectAllFiles: document.getElementById('selectAllFiles'),
    batchFilterBtn: document.getElementById('batchFilterBtn'),
    deleteSelectedBtn: document.getElementById('deleteSelectedBtn'),
    filterSection: document.getElementById('filterSection'),
    filterForm: document.getElementById('filterForm'),
    optionalFilters: document.getElementById('optionalFilters'),
    displayFields: document.getElementById('displayFields'),
    selectedFilesInfo: document.getElementById('selectedFilesInfo'),
    farmId: document.getElementById('farmId'),
    resultSection: document.getElementById('resultSection'),
    alertContainer: document.getElementById('alertContainer'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    downloadBtn: document.getElementById('downloadBtn'),
    selectedFileId: document.getElementById('selectedFileId')
};

// 浏览器关闭检测（无网络请求方案）
let isPageVisible = true;
let visibilityChangeCount = 0;

function handleVisibilityChange() {
    if (document.hidden) {
        // 页面被隐藏（可能是切换标签页或最小化）
        isPageVisible = false;
        visibilityChangeCount++;
        
        // 延迟检测：如果3秒后页面还是隐藏状态，发送关闭信号
        setTimeout(() => {
            if (document.hidden) {
                sendCloseSignal();
            }
        }, 3000);
    } else {
        // 页面重新可见
        isPageVisible = true;
    }
}

function sendCloseSignal() {
    // 发送关闭信号给后端
    try {
        fetch(`${API_BASE}/close-signal`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'close' })
        }).catch(() => {}); // 忽略错误
    } catch (error) {
        // 静默处理
    }
}

// 页面关闭时发送信号
window.addEventListener('beforeunload', () => {
    sendCloseSignal();
});

window.addEventListener('unload', () => {
    sendCloseSignal();
});

// 监听页面可见性变化
document.addEventListener('visibilitychange', handleVisibilityChange);

// 服务器连接检测
let connectionCheckInterval = null;
let isServerReady = false;

async function checkServerConnection() {
    try {
        updateLoadingStatus('正在连接服务器...');
        
        // 使用AbortController来实现超时，兼容性更好
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        
        const response = await fetch(`/health`, {
            method: 'GET',
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            updateLoadingStatus('服务器连接成功！');
            isServerReady = true;
            if (connectionCheckInterval) {
                clearInterval(connectionCheckInterval);
                connectionCheckInterval = null;
            }
            // 稍等一下再隐藏消息，让用户看到成功状态
            setTimeout(() => {
                hideServerLoadingMessage();
                // 初始化应用
                initializeApp();
            }, 500);
            return true;
        } else {
            updateLoadingStatus(`服务器响应异常 (${response.status})`);
        }
    } catch (error) {
        console.debug('服务器尚未就绪，继续等待...', error.name);
        if (error.name === 'AbortError') {
            updateLoadingStatus('连接超时，继续尝试...');
        } else {
            updateLoadingStatus('等待服务器启动...');
        }
    }
    return false;
}

function showServerLoadingMessage() {
    // 在页面顶部显示服务器加载提示
    const existingMessage = document.getElementById('server-loading-message');
    if (!existingMessage) {
        const message = document.createElement('div');
        message.id = 'server-loading-message';
        message.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #007bff;
            color: white;
            text-align: center;
            padding: 10px;
            z-index: 10000;
            font-family: Arial, sans-serif;
        `;
        message.innerHTML = `
            <i class="spinner-border spinner-border-sm me-2" role="status"></i>
            DHI蛋白筛查系统正在启动，请稍候... <span id="loading-status">检查服务器状态</span>
        `;
        document.body.insertBefore(message, document.body.firstChild);
    }
}

function hideServerLoadingMessage() {
    const message = document.getElementById('server-loading-message');
    if (message) {
        message.remove();
    }
}

function updateLoadingStatus(text) {
    const statusElement = document.getElementById('loading-status');
    if (statusElement) {
        statusElement.textContent = text;
    }
}

function initializeApp() {
    initializeEventListeners();
    loadAvailableFilters();
    loadUploadedFiles();
    loadFarmIds();
    
    console.log('DHI蛋白筛查系统已加载完成');
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 立即检查服务器连接
    checkServerConnection().then(ready => {
        if (!ready) {
            // 服务器还没就绪，显示加载提示并开始轮询
            showServerLoadingMessage();
            connectionCheckInterval = setInterval(checkServerConnection, 1000); // 改为1秒检查一次
        }
    });
});

// 初始化事件监听器
function initializeEventListeners() {
    // 文件选择
    elements.selectFileBtn.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // 拖拽上传
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleFileDrop);
    
    // 文件列表选择
    if (elements.selectAllFiles) {
        elements.selectAllFiles.addEventListener('change', handleSelectAllFiles);
    }
    
    if (elements.batchFilterBtn) {
        elements.batchFilterBtn.addEventListener('click', handleBatchFilter);
    }
    
    if (elements.deleteSelectedBtn) {
        elements.deleteSelectedBtn.addEventListener('click', handleDeleteSelected);
    }
    
    // 筛选表单
    elements.filterForm.addEventListener('submit', handleFilterSubmit);
}

// 显示消息
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    elements.alertContainer.innerHTML = alertHtml;
    
    // 自动消失
    setTimeout(() => {
        const alert = elements.alertContainer.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// 显示/隐藏加载指示器
function showLoading(show = true) {
    elements.loadingOverlay.style.display = show ? 'flex' : 'none';
    
    if (!show) {
        // 停止监控进度
        stopGlobalProgressMonitoring();
    }
}

// 开始全局进度监控
function startGlobalProgressMonitoring() {
    if (globalProgressInterval) {
        clearInterval(globalProgressInterval);
    }
    
    const loadingText = document.getElementById('loadingText');
    const loadingTimeInfo = document.getElementById('loadingTimeInfo');
    
    console.log('开始进度监控，当前显示文本:', loadingText?.textContent);
    
    // 立即执行第一次检查
    updateProgressDisplay();
    
    // 然后定期检查
    setTimeout(() => {
        console.log('延迟1秒后开始定期监控');
    }, 1000);
    
    // 设置定期检查
    globalProgressInterval = setInterval(updateProgressDisplay, 1000); // 每1秒更新一次
    
    let retryCount = 0;
    
    async function updateProgressDisplay() {
        try {
            console.log('正在获取进度信息...');
            const response = await fetch(`${API_BASE}/processing-progress`);
            const progress = await response.json();
            
            console.log('进度监控数据:', {
                is_processing: progress.is_processing,
                current_step: progress.current_step,
                progress_percentage: progress.progress_percentage,
                current_file: progress.current_file,
                elapsed_time: progress.elapsed_time,
                remaining_time: progress.estimated_remaining_time
            });
            
            if (progress.is_processing) {
                // 重置重试计数
                retryCount = 0;
                
                // 更新主要状态文本
                let mainText = progress.current_step || '初始化';
                if (progress.current_file) {
                    mainText += ` - ${progress.current_file}`;
                }
                loadingText.textContent = mainText;
                
                // 更新时间信息
                let timeInfo = '';
                if (progress.elapsed_time_formatted) {
                    timeInfo += `已用时: ${progress.elapsed_time_formatted}`;
                }
                if (progress.remaining_time_formatted) {
                    if (timeInfo) timeInfo += ' | ';
                    timeInfo += `预计剩余: ${progress.remaining_time_formatted}`;
                }
                if (progress.progress_percentage !== undefined) {
                    if (timeInfo) timeInfo += ' | ';
                    timeInfo += `进度: ${progress.progress_percentage}%`;
                }
                
                loadingTimeInfo.textContent = timeInfo;
                
                console.log('界面已更新:', {
                    mainText,
                    timeInfo,
                    progress: progress.progress_percentage
                });
            } else {
                console.log('后端返回非处理状态，停止监控');
                // 处理完成，停止监控
                stopGlobalProgressMonitoring();
            }
        } catch (error) {
            retryCount++;
            console.warn(`第${retryCount}次进度监控失败:`, error);
            
            // 前几次重试时保持原状态，避免频繁变更显示内容
            if (retryCount <= 3) {
                console.log('保持当前显示状态，继续重试...');
                return;
            }
            
            // 多次失败后显示通用等待信息
            if (loadingText && !loadingText.textContent.includes('获取进度信息')) {
                loadingText.textContent = '正在处理，获取进度信息中...';
                loadingTimeInfo.textContent = '连接后端服务...';
            }
        }
    }
}

// 停止全局进度监控
function stopGlobalProgressMonitoring() {
    if (globalProgressInterval) {
        clearInterval(globalProgressInterval);
        globalProgressInterval = null;
    }
    
    // 不重置显示文本，让最后的状态保持显示
    console.log('进度监控已停止');
}

// 更新步骤状态
function updateStep(step) {
    // 移除所有步骤的active状态
    for (let i = 1; i <= 3; i++) {
        const stepElement = document.getElementById(`step${i}`);
        stepElement.classList.remove('active', 'completed');
        
        if (i < step) {
            stepElement.classList.add('completed');
        } else if (i === step) {
            stepElement.classList.add('active');
        }
    }
    
    currentStep = step;
    
    // 显示/隐藏相应的部分
    elements.filterSection.style.display = step >= 2 ? 'block' : 'none';
    elements.resultSection.style.display = step >= 3 ? 'block' : 'none';
}

// 处理文件选择
function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
        if (files.length === 1) {
            uploadFile(files[0]);
        } else {
            uploadBatchFiles(files);
        }
    }
}

// 处理拖拽
function handleDragOver(event) {
    event.preventDefault();
    elements.uploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    elements.uploadArea.classList.remove('dragover');
}

function handleFileDrop(event) {
    event.preventDefault();
    elements.uploadArea.classList.remove('dragover');
    
    const files = Array.from(event.dataTransfer.files);
    if (files.length > 0) {
        if (files.length === 1) {
            uploadFile(files[0]);
        } else {
            uploadBatchFiles(files);
        }
    }
}

// 上传文件
async function uploadFile(file) {
    if (!file) return;
    
    // 检查文件类型
    const allowedTypes = ['.zip', '.xlsx'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        showAlert('仅支持ZIP和XLSX文件格式', 'danger');
        return;
    }
    
    // 检查文件大小 (100MB)
    if (file.size > 100 * 1024 * 1024) {
        showAlert('文件大小不能超过100MB', 'danger');
        return;
    }
    
    try {
        // 显示上传进度
        elements.uploadArea.classList.add('uploading');
        elements.uploadProgress.style.display = 'block';
        
        const progressBar = elements.uploadProgress.querySelector('.progress-bar');
        const statusText = elements.uploadProgress.querySelector('.upload-status');
        
        statusText.textContent = '准备上传...';
        progressBar.style.width = '0%';
        
        // 创建FormData
        const formData = new FormData();
        formData.append('file', file);
        
        // 模拟进度
        progressBar.style.width = '20%';
        statusText.textContent = '上传中...';
        
        // 上传文件
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        progressBar.style.width = '80%';
        statusText.textContent = '处理文件...';
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '上传失败');
        }
        
        const result = await response.json();
        
        if (result.success) {
            progressBar.style.width = '100%';
            statusText.textContent = '上传完成';
            
            showAlert(result.message, 'success');
            
            // 重新加载文件列表和数据统计信息
            await loadUploadedFiles();
            await loadDataStatistics();
            
        } else {
            throw new Error(result.message || '上传失败');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        showAlert(error.message, 'danger');
    } finally {
        // 隐藏上传进度
        setTimeout(() => {
            elements.uploadArea.classList.remove('uploading');
            elements.uploadProgress.style.display = 'none';
        }, 2000);
        elements.fileInput.value = '';
    }
}

// 批量上传文件
async function uploadBatchFiles(files) {
    if (!files || files.length === 0) return;
    
    // 检查文件类型
    const allowedTypes = ['.zip', '.xlsx'];
    for (const file of files) {
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(fileExtension)) {
            showAlert(`文件 ${file.name} 格式不支持，仅支持ZIP和XLSX文件`, 'danger');
            return;
        }
        
        // 检查文件大小 (100MB)
        if (file.size > 100 * 1024 * 1024) {
            showAlert(`文件 ${file.name} 大小超过100MB`, 'danger');
            return;
        }
    }
    
    try {
        // 显示上传进度
        elements.uploadArea.classList.add('uploading');
        elements.uploadProgress.style.display = 'block';
        
        const progressBar = elements.uploadProgress.querySelector('.progress-bar');
        const statusText = elements.uploadProgress.querySelector('.upload-status');
        
        statusText.textContent = `准备批量上传 ${files.length} 个文件...`;
        progressBar.style.width = '0%';
        
        // 创建FormData
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        
        // 开始监控进度
        const progressInterval = setInterval(async () => {
            try {
                const progressResponse = await fetch(`${API_BASE}/processing-progress`);
                const progress = await progressResponse.json();
                
                if (progress.is_processing) {
                    progressBar.style.width = `${progress.progress_percentage}%`;
                    
                    // 构建状态文本，包含时间信息
                    let statusTextValue = `${progress.current_step}`;
                    
                    if (progress.current_file) {
                        statusTextValue += ` - ${progress.current_file}`;
                    }
                    
                    // 添加时间信息
                    if (progress.remaining_time_formatted) {
                        statusTextValue += ` | 预计剩余: ${progress.remaining_time_formatted}`;
                    }
                    
                    if (progress.elapsed_time_formatted) {
                        statusTextValue += ` | 已用时: ${progress.elapsed_time_formatted}`;
                    }
                    
                    statusText.textContent = statusTextValue;
                    
                    // 在控制台显示详细信息用于调试
                    console.log('处理进度:', {
                        percentage: progress.progress_percentage,
                        step: progress.current_step,
                        remaining: progress.remaining_time_formatted,
                        elapsed: progress.elapsed_time_formatted,
                        total_estimated: progress.total_time_formatted
                    });
                } else {
                    clearInterval(progressInterval);
                }
            } catch (e) {
                console.warn('Progress update failed:', e);
            }
        }, 500);
        
        // 批量上传文件
        const response = await fetch(`${API_BASE}/upload/batch`, {
            method: 'POST',
            body: formData
        });
        
        // 停止进度监控
        clearInterval(progressInterval);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '批量上传失败');
        }
        
        const result = await response.json();
        
        if (result.success) {
            const successCount = result.success_files.length;
            const failCount = result.failed_files.length;
            
            // 显示最终进度
            progressBar.style.width = '100%';
            statusText.textContent = '上传完成';
            
            let message = `批量上传完成：成功 ${successCount} 个`;
            if (failCount > 0) {
                message += `，失败 ${failCount} 个`;
            }
            
            showAlert(message, successCount > 0 ? 'success' : 'warning');
            
            // 显示失败文件的详细信息
            if (result.failed_files.length > 0) {
                const failedDetails = result.failed_files.map(f => `${f.filename}: ${f.error}`).join('<br>');
                showAlert(`失败文件详情：<br>${failedDetails}`, 'warning');
            }
            
            // 重新加载文件列表和数据统计信息
            await loadUploadedFiles();
            await loadDataStatistics();
            
        } else {
            throw new Error(result.message || '批量上传失败');
        }
        
    } catch (error) {
        console.error('Batch upload error:', error);
        showAlert(error.message, 'danger');
    } finally {
        // 隐藏上传进度
        setTimeout(() => {
            elements.uploadArea.classList.remove('uploading');
            elements.uploadProgress.style.display = 'none';
        }, 2000);
        elements.fileInput.value = '';
    }
}

// 加载已上传的文件列表
async function loadUploadedFiles() {
    try {
        const response = await fetch(`${API_BASE}/files`);
        const result = await response.json();
        
        if (result.success) {
            uploadedFiles = result.files;
            updateFileList();
        }
    } catch (error) {
        console.error('Load files error:', error);
    }
}

// 更新文件列表显示
function updateFileList() {
    if (uploadedFiles.length === 0) {
        elements.fileListSection.style.display = 'none';
        return;
    }
    
    elements.fileListSection.style.display = 'block';
    
    const tbody = elements.fileList;
    tbody.innerHTML = '';
    
    uploadedFiles.forEach(file => {
        const row = document.createElement('tr');
        row.className = 'file-row';
        row.dataset.fileId = file.file_id;
        
        const uploadTime = new Date(file.upload_time).toLocaleString('zh-CN');
        
                    row.innerHTML = `
            <td>
                <input type="checkbox" class="form-check-input file-checkbox" 
                       value="${file.file_id}" onchange="updateFileSelection()">
            </td>
            <td>${file.filename}</td>
            <td>${uploadTime}</td>
            <td>${file.detected_date || '未识别'}</td>
            <td>${file.row_count || 0}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteFile('${file.file_id}')">
                    删除
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    updateFileSelectionUI();
}



// 处理全选/取消全选
function handleSelectAllFiles(event) {
    const checkboxes = document.querySelectorAll('.file-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = event.target.checked;
    });
    updateFileSelection();
}

// 更新文件选择状态
function updateFileSelection() {
    const checkboxes = document.querySelectorAll('.file-checkbox:checked');
    selectedFiles = Array.from(checkboxes).map(cb => cb.value);
    
    updateFileSelectionUI();
    updateSelectedFilesInfo();
}

// 更新文件选择UI状态
function updateFileSelectionUI() {
    const hasSelected = selectedFiles.length > 0;
    
    if (elements.batchFilterBtn) {
        elements.batchFilterBtn.style.display = hasSelected ? 'inline-block' : 'none';
    }
    
    if (elements.deleteSelectedBtn) {
        elements.deleteSelectedBtn.style.display = hasSelected ? 'inline-block' : 'none';
    }
    
    // 更新全选复选框状态
    const allCheckboxes = document.querySelectorAll('.file-checkbox');
    const checkedCheckboxes = document.querySelectorAll('.file-checkbox:checked');
    
    if (elements.selectAllFiles) {
        elements.selectAllFiles.indeterminate = 
            checkedCheckboxes.length > 0 && checkedCheckboxes.length < allCheckboxes.length;
        elements.selectAllFiles.checked = 
            allCheckboxes.length > 0 && checkedCheckboxes.length === allCheckboxes.length;
    }
}

// 更新选中文件信息显示
function updateSelectedFilesInfo() {
    if (!elements.selectedFilesInfo) return;
    
    if (selectedFiles.length === 0) {
        elements.selectedFilesInfo.innerHTML = '<p class="text-muted mb-0">请先选择要筛选的文件</p>';
        return;
    }
    
    const selectedFileInfos = uploadedFiles.filter(f => selectedFiles.includes(f.file_id));
    
    let html = `<strong>已选择 ${selectedFiles.length} 个文件：</strong><br>`;
    html += '<div class="row mt-2">';
    
    selectedFileInfos.forEach(file => {
        html += `
            <div class="col-md-6 mb-2">
                <div class="border rounded p-2 bg-white">
                    <small class="text-primary fw-bold">${file.filename}</small><br>
                    <small class="text-muted">
                        ${file.detected_date || '未识别日期'} | ${file.row_count || 0} 行数据
                    </small>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    elements.selectedFilesInfo.innerHTML = html;
}



// 加载牛场编号
async function loadFarmIds() {
    try {
        const response = await fetch(`${API_BASE}/farm-ids`);
        const result = await response.json();
        
        if (result.success) {
            farmIds = result.farm_ids;
            updateFarmIdOptions();
        }
    } catch (error) {
        console.error('Load farm IDs error:', error);
    }
}

// 加载数据统计信息并设置默认筛选范围
async function loadDataStatistics() {
    try {
        const response = await fetch(`${API_BASE}/data-statistics`);
        const result = await response.json();
        
        if (result.success) {
            // 设置日期范围默认值
            if (result.date_range) {
                document.getElementById('startDate').value = result.date_range.min;
                document.getElementById('endDate').value = result.date_range.max;
            }
            
            // 设置蛋白率范围默认值
            if (result.protein_range) {
                document.getElementById('proteinMin').value = result.protein_range.min;
                document.getElementById('proteinMax').value = result.protein_range.max;
            }
            
            // 设置胎次范围默认值
            if (result.parity_range) {
                document.getElementById('parityMin').value = result.parity_range.min;
                document.getElementById('parityMax').value = result.parity_range.max;
            }
            
            // 更新牛场编号
            if (result.farm_ids) {
                farmIds = result.farm_ids;
                updateFarmIdOptions();
            }
            
            console.log('数据统计信息已加载:', result);
        }
    } catch (error) {
        console.error('Load data statistics error:', error);
    }
}

// 更新牛场编号选项
function updateFarmIdOptions() {
    if (!elements.farmId) return;
    
    elements.farmId.innerHTML = '';
    
    if (farmIds.length === 0) {
        elements.farmId.innerHTML = '<option value="">暂无牛场数据</option>';
        return;
    }
    
    farmIds.forEach(farmId => {
        const option = document.createElement('option');
        option.value = farmId;
        option.textContent = farmId;
        elements.farmId.appendChild(option);
    });
}

// 处理批量筛选
function handleBatchFilter() {
    if (selectedFiles.length === 0) {
        showAlert('请先选择要筛选的文件', 'warning');
        return;
    }
    
    updateSelectedFilesInfo();
    updateStep(2);
    showAlert(`已选择 ${selectedFiles.length} 个文件，请设置筛选条件`, 'info');
}

// 处理删除选中文件
async function handleDeleteSelected() {
    if (selectedFiles.length === 0) {
        showAlert('请先选择要删除的文件', 'warning');
        return;
    }
    
    if (!confirm(`确定要删除选中的 ${selectedFiles.length} 个文件吗？`)) return;
    
    try {
        showLoading(true);
        
        // 逐个删除文件
        const deletePromises = selectedFiles.map(fileId => 
            fetch(`${API_BASE}/files/${fileId}`, { method: 'DELETE' })
        );
        
        const responses = await Promise.all(deletePromises);
        const results = await Promise.all(responses.map(r => r.json()));
        
        const successCount = results.filter(r => r.success).length;
        const failCount = results.length - successCount;
        
        let message = `删除完成：成功 ${successCount} 个`;
        if (failCount > 0) {
            message += `，失败 ${failCount} 个`;
        }
        
        showAlert(message, successCount > 0 ? 'success' : 'danger');
        
        // 重新加载文件列表和数据统计信息
        selectedFiles = [];
        await loadUploadedFiles();
        await loadDataStatistics();
        
    } catch (error) {
        console.error('Delete selected files error:', error);
        showAlert('删除文件时出错：' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}



// 删除文件
async function deleteFile(fileId) {
    if (!confirm('确定要删除这个文件吗？')) return;
    
    try {
        const response = await fetch(`${API_BASE}/files/${fileId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('文件已删除', 'success');
            uploadedFiles = uploadedFiles.filter(f => f.file_id !== fileId);
            updateFileList();
            
            // 重新加载数据统计信息
            await loadDataStatistics();
            
            // 如果删除的是当前选择的文件，重置状态
            if (selectedFileId === fileId) {
                selectedFileId = null;
                updateStep(1);
            }
        } else {
            throw new Error(result.message || '删除失败');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showAlert(error.message, 'danger');
    }
}

// 加载可用的筛选条件
async function loadAvailableFilters() {
    try {
        const response = await fetch(`${API_BASE}/filters`);
        const result = await response.json();
        
        if (result.success) {
            availableFilters = result.filters;
            generateOptionalFilters();
        }
    } catch (error) {
        console.error('Load filters error:', error);
    }
}

// 生成可选筛选条件UI - 简化版本，不需要可选条件
function generateOptionalFilters() {
    // 新需求下不需要可选筛选条件，保留函数以避免调用错误
    generateDisplayFields();
}

// 生成显示字段选择UI - 简化版本，固定显示蛋白率
function generateDisplayFields() {
    // 新需求下固定显示蛋白率，不需要UI选择
    // 保留函数以避免调用错误，但内容为空
}

// 切换筛选条件启用状态
function toggleFilter(field) {
    const checkbox = document.getElementById(`enable_${field}`);
    const controls = document.getElementById(`controls_${field}`);
    
    if (checkbox.checked) {
        controls.style.display = 'block';
    } else {
        controls.style.display = 'none';
    }
}

// 处理筛选表单提交
async function handleFilterSubmit(event) {
    event.preventDefault();
    
    // 清除之前的筛选结果
    clearPreviousResults();
    
    // 显示正在应用筛选条件的提示
    showAlert('正在应用新的筛选条件...', 'info');
    
    // 检查是单文件还是批量模式
    if (selectedFiles.length > 0) {
        // 批量筛选模式
        await handleBatchFilterSubmit();
    } else if (selectedFileId) {
        // 单文件模式（保留兼容性）
        await handleSingleFilterSubmit();
    } else {
        showAlert('请先选择要筛选的文件', 'warning');
    }
}

// 清除之前的筛选结果
function clearPreviousResults() {
    // 隐藏结果部分
    elements.resultSection.style.display = 'none';
    
    // 清空结果信息
    const resultInfo = document.getElementById('resultInfo');
    const downloadArea = document.getElementById('downloadArea');
    
    if (resultInfo) {
        resultInfo.innerHTML = '';
    }
    
    if (downloadArea) {
        downloadArea.style.display = 'none';
    }
    
    // 重置下载按钮
    if (elements.downloadBtn) {
        elements.downloadBtn.href = '#';
    }
}

// 处理单文件筛选
async function handleSingleFilterSubmit() {
    try {
        showLoading(true);
        
        // 构建筛选条件
        const filters = buildFilterConfig();
        
        const requestData = {
            file_id: selectedFileId,
            filters: filters
        };
        
        const response = await fetch(`${API_BASE}/filter`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '筛选失败');
        }
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            displayResults(result);
            updateStep(3);
        } else {
            throw new Error(result.message || '筛选失败');
        }
        
    } catch (error) {
        console.error('Filter error:', error);
        showAlert(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// 处理批量筛选
async function handleBatchFilterSubmit() {
    try {
        // 显示加载界面但先不开始进度监控
        elements.loadingOverlay.style.display = 'flex';
        
        // 手动设置初始状态
        const loadingText = document.getElementById('loadingText');
        const loadingTimeInfo = document.getElementById('loadingTimeInfo');
        if (loadingText) {
            loadingText.textContent = '正在启动筛选处理...';
            console.log('已设置初始状态文本:', loadingText.textContent);
        }
        if (loadingTimeInfo) {
            loadingTimeInfo.textContent = '准备中，请稍候...';
            console.log('已设置初始时间信息:', loadingTimeInfo.textContent);
        }
        
        // 构建筛选条件
        const filters = buildFilterConfig();
        console.log('筛选条件已构建:', filters);
        
        // 获取选中的显示字段
        const displayFields = getSelectedDisplayFields();
        
        // 准备表单数据
        const formData = new FormData();
        
        // 添加选中的文件
        selectedFiles.forEach(fileId => {
            formData.append('selected_files', fileId);
        });
        
        // 添加筛选条件
        formData.append('filters', JSON.stringify(filters));
        
        // 添加显示字段
        displayFields.forEach(field => {
            formData.append('display_fields', field);
        });
        
        // 添加符合条件月份数
        const minMatchMonths = document.getElementById('minMatchMonths').value || 3;
        formData.append('min_match_months', minMatchMonths);
        
        console.log('正在发送筛选请求...');
        
        // 发送请求后立即开始进度监控
        const responsePromise = fetch(`${API_BASE}/filter/batch`, {
            method: 'POST',
            body: formData
        });
        
        // 等待一小段时间让后端开始处理，然后启动进度监控
        setTimeout(() => {
            console.log('开始进度监控...');
            startGlobalProgressMonitoring();
        }, 500);
        
        const response = await responsePromise;
        console.log('请求响应状态:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '批量筛选失败');
        }
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            displayResults(result);
            updateStep(3);
            
            // 确保进度监控停止
            stopGlobalProgressMonitoring();
        } else {
            throw new Error(result.message || '批量筛选失败');
        }
        
    } catch (error) {
        console.error('Batch filter error:', error);
        showAlert(error.message, 'danger');
        
        // 确保进度监控停止
        stopGlobalProgressMonitoring();
    } finally {
        showLoading(false);
    }
}

// 获取选中的显示字段 - 简化版本，固定返回蛋白率
function getSelectedDisplayFields() {
    const baseFields = ['farm_id', 'management_id', 'parity'];
    const fixedFields = ['protein_pct']; // 固定显示蛋白率
    
    return [...baseFields, ...fixedFields];
}

// 构建筛选条件配置
function buildFilterConfig() {
    // 确保读取最新的表单值
            console.log('构建筛选条件，当前表单值：');
        console.log('- 蛋白率范围:', document.getElementById('proteinMin').value, '-', document.getElementById('proteinMax').value);
        console.log('- 空值处理:', document.getElementById('includeNullAsMatch').checked);
        console.log('- 胎次范围:', document.getElementById('parityMin').value, '-', document.getElementById('parityMax').value);
        console.log('- 符合月份数:', document.getElementById('minMatchMonths').value);
        console.log('- 选中文件数:', selectedFiles.length);
    
    const filters = {};
    
    // 必选条件
    filters.date_range = {
        field: 'sample_date',
        enabled: true,
        required: true,
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value
    };
    
    const farmIdSelect = document.getElementById('farmId');
    const selectedFarmIds = Array.from(farmIdSelect.selectedOptions).map(option => option.value);
    filters.farm_id = {
        field: 'farm_id',
        enabled: true,
        required: true,
        allowed: selectedFarmIds
    };
    
    filters.parity = {
        field: 'parity',
        enabled: true,
        required: true,
        min: parseFloat(document.getElementById('parityMin').value),
        max: parseFloat(document.getElementById('parityMax').value)
    };
    
    filters.protein_pct = {
        field: 'protein_pct',
        enabled: true,
        required: true,
        min: parseFloat(document.getElementById('proteinMin').value),
        max: parseFloat(document.getElementById('proteinMax').value),
        include_null_as_match: document.getElementById('includeNullAsMatch').checked
    };
    
    // 可选条件
    Object.entries(availableFilters).forEach(([filterName, config]) => {
        const field = config.field || filterName;
        const checkbox = document.getElementById(`enable_${field}`);
        
        if (checkbox && checkbox.checked) {
            const minInput = document.getElementById(`min_${field}`);
            const maxInput = document.getElementById(`max_${field}`);
            
            filters[field] = {
                field: field,
                enabled: true,
                required: false,
                min: minInput ? parseFloat(minInput.value) : undefined,
                max: maxInput ? parseFloat(maxInput.value) : undefined
            };
        }
    });
    
    return filters;
}

// 显示筛选结果
function displayResults(result) {
    const resultInfo = document.getElementById('resultInfo');
    const downloadArea = document.getElementById('downloadArea');
    
    // 检查是否有新的统计数据格式
    if (result.original_cow_count !== undefined) {
        // 使用新的4组统计数据
        resultInfo.innerHTML = `
            <div class="row mb-3">
                <div class="col-md-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title">全部数据</h6>
                            <h3 class="text-primary">${result.original_cow_count}</h3>
                            <p class="card-text small">所有上传文件的牛头数</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title">筛选范围</h6>
                            <h3 class="text-info">${result.range_cow_count}</h3>
                            <p class="card-text small">选中文件的牛头数</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title">筛选结果</h6>
                            <h3 class="text-success">${result.final_cow_count}</h3>
                            <p class="card-text small">符合条件的牛头数</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h6 class="card-title">筛选率</h6>
                            <h3 class="text-warning">${result.filter_rate}%</h3>
                            <p class="card-text small">符合条件占全部数据比例</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i>
                <strong>统计说明：</strong>
                牛头数统计基于"牛场编号+管理号"的唯一组合。筛选率 = 符合条件的牛头数 ÷ 全部数据的牛头数 × 100%
            </div>
        `;
    } else {
        // 使用原有的统计数据格式（兼容老版本）
    resultInfo.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <h5 class="card-title">原始数据</h5>
                        <h2 class="text-primary">${result.total_rows}</h2>
                        <p class="card-text">总行数</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <h5 class="card-title">筛选结果</h5>
                        <h2 class="text-success">${result.filtered_rows}</h2>
                        <p class="card-text">符合条件的行数</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-light">
                    <div class="card-body text-center">
                        <h5 class="card-title">筛选率</h5>
                        <h2 class="text-info">${((result.filtered_rows / result.total_rows) * 100).toFixed(1)}%</h2>
                        <p class="card-text">数据保留率</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    }
    
    if (result.download_url) {
        elements.downloadBtn.href = result.download_url;
        downloadArea.style.display = 'block';
    }
}



// 设置默认日期
function setDefaultDates() {
    const today = new Date();
    const startOfYear = new Date(today.getFullYear(), 0, 1);
    
    document.getElementById('startDate').value = startOfYear.toISOString().split('T')[0];
    document.getElementById('endDate').value = today.toISOString().split('T')[0];
}

// 页面加载完成后加载数据统计信息
document.addEventListener('DOMContentLoaded', function() {
    // 先设置基本默认值，然后尝试加载实际统计信息
    setDefaultDates();
    loadDataStatistics();
}); 