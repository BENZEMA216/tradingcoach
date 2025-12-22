import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { uploadApi } from '@/api/client';
import type { UploadResponse, UploadHistoryItem } from '@/api/client';
import {
  Upload as UploadIcon,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  Loader2,
  History,
  ArrowRight,
  FileSpreadsheet,
} from 'lucide-react';
import { formatNumber, formatDate } from '@/utils/format';
import { useNavigate } from 'react-router-dom';

export function Upload() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);

  // Get upload history
  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['upload', 'history'],
    queryFn: () => uploadApi.getHistory(10),
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadApi.uploadTrades(file),
    onSuccess: (data) => {
      setUploadResult(data);
      setSelectedFile(null);
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['statistics'] });
      queryClient.invalidateQueries({ queryKey: ['upload', 'history'] });
    },
  });

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.csv')) {
        setSelectedFile(file);
        setUploadResult(null);
      }
    }
  }, []);

  // Handle file input change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadResult(null);
    }
  };

  // Handle upload
  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate(selectedFile);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('upload.title', 'Upload Trades')}
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          {t('upload.subtitle', 'Import your trading history from CSV file')}
        </p>
      </div>

      {/* Upload Area */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div
          className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />

          <div className="flex flex-col items-center space-y-4">
            <div className={`p-4 rounded-full ${
              dragActive ? 'bg-blue-100 dark:bg-blue-900/50' : 'bg-gray-100 dark:bg-gray-700'
            }`}>
              <UploadIcon className={`w-8 h-8 ${
                dragActive ? 'text-blue-600' : 'text-gray-500'
              }`} />
            </div>

            <div>
              <p className="text-lg font-medium text-gray-900 dark:text-white">
                {t('upload.dragDrop', 'Drag and drop your CSV file here')}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {t('upload.orClick', 'or click to browse')}
              </p>
            </div>

            <p className="text-xs text-gray-400">
              {t('upload.supportedFormats', 'Supports Futu Securities CSV export (Chinese/English)')}
            </p>
          </div>
        </div>

        {/* Selected File */}
        {selectedFile && (
          <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileSpreadsheet className="w-8 h-8 text-green-600" />
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>

            <button
              onClick={handleUpload}
              disabled={uploadMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t('upload.processing', 'Processing...')}</span>
                </>
              ) : (
                <>
                  <UploadIcon className="w-4 h-4" />
                  <span>{t('upload.uploadBtn', 'Upload')}</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Upload Result */}
        {uploadResult && (
          <div className={`mt-4 p-4 rounded-lg ${
            uploadResult.success
              ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
              : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
          }`}>
            <div className="flex items-start space-x-3">
              {uploadResult.success ? (
                <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              )}
              <div className="flex-1">
                <p className={`font-medium ${
                  uploadResult.success ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'
                }`}>
                  {uploadResult.message}
                </p>

                {/* Stats */}
                <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('upload.totalRows', 'Total Rows')}
                    </p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {formatNumber(uploadResult.total_rows)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('upload.newTrades', 'New Trades')}
                    </p>
                    <p className="text-lg font-semibold text-green-600">
                      +{formatNumber(uploadResult.new_trades)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('upload.duplicatesSkipped', 'Duplicates Skipped')}
                    </p>
                    <p className="text-lg font-semibold text-gray-500">
                      {formatNumber(uploadResult.duplicates_skipped)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('upload.processingTime', 'Processing Time')}
                    </p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {uploadResult.processing_time_ms}ms
                    </p>
                  </div>
                </div>

                {/* Additional Info */}
                {uploadResult.positions_matched > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {t('upload.positionsMatched', 'Positions matched')}: {uploadResult.positions_matched} |{' '}
                      {t('upload.positionsScored', 'Positions scored')}: {uploadResult.positions_scored}
                    </p>
                  </div>
                )}

                {/* View Results Button */}
                {uploadResult.new_trades > 0 && (
                  <div className="mt-4">
                    <button
                      onClick={() => navigate('/positions')}
                      className="inline-flex items-center space-x-2 text-blue-600 hover:text-blue-700"
                    >
                      <span>{t('upload.viewPositions', 'View Positions')}</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {uploadMutation.isError && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div>
                <p className="font-medium text-red-800 dark:text-red-200">
                  {t('upload.error', 'Upload failed')}
                </p>
                <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                  {(uploadMutation.error as Error)?.message || 'Unknown error'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Upload History */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex items-center space-x-3 mb-4">
          <History className="w-5 h-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('upload.history', 'Import History')}
          </h2>
        </div>

        {historyLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : history && history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <th className="pb-3 pr-4">{t('upload.historyDate', 'Date')}</th>
                  <th className="pb-3 pr-4">{t('upload.historyFile', 'File')}</th>
                  <th className="pb-3 pr-4">{t('upload.historyType', 'Type')}</th>
                  <th className="pb-3 pr-4 text-right">{t('upload.historyNew', 'New')}</th>
                  <th className="pb-3 pr-4 text-right">{t('upload.historySkipped', 'Skipped')}</th>
                  <th className="pb-3">{t('upload.historyStatus', 'Status')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {history.map((item: UploadHistoryItem) => (
                  <tr key={item.id} className="text-sm">
                    <td className="py-3 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4" />
                        <span>{formatDate(item.import_time)}</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-gray-900 dark:text-white max-w-[200px] truncate">
                      {item.file_name}
                    </td>
                    <td className="py-3 pr-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        item.file_type === 'english'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                          : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                      }`}>
                        {item.file_type === 'english' ? 'EN' : 'CN'}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-right font-medium text-green-600">
                      +{item.new_trades}
                    </td>
                    <td className="py-3 pr-4 text-right text-gray-500">
                      {item.duplicates_skipped}
                    </td>
                    <td className="py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        item.status === 'success'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                          : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>{t('upload.noHistory', 'No import history yet')}</p>
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 border border-blue-100 dark:border-blue-800">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
          {t('upload.howTo', 'How to export from Futu')}
        </h3>
        <ol className="text-sm text-blue-800 dark:text-blue-200 space-y-1 list-decimal list-inside">
          <li>{t('upload.step1', 'Open Futu Trading App or Web')}</li>
          <li>{t('upload.step2', 'Go to Trade History')}</li>
          <li>{t('upload.step3', 'Click Export and select CSV format')}</li>
          <li>{t('upload.step4', 'Upload the downloaded file here')}</li>
        </ol>
      </div>
    </div>
  );
}
