import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileText, Clock, User, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import SignatureCanvas from './SignatureCanvas';
import { apiClient } from '../../lib/api';

const SignDocument = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const [signatureData, setSignatureData] = useState(null);
  const [documentData, setDocumentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [signing, setSigning] = useState(false);
  const [declining, setDeclining] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [declineReason, setDeclineReason] = useState('');
  const [showDeclineForm, setShowDeclineForm] = useState(false);

  useEffect(() => {
    loadSignatureDetails();
  }, [token]);

  const loadSignatureDetails = async () => {
    try {
      const response = await fetch(`/api/signatures/sign/${token}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to load signature details');
      }

      setDocumentData(data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignatureChange = (signature) => {
    setSignatureData(signature);
  };

  const handleSign = async () => {
    if (!signatureData) {
      setError('Por favor, desenhe sua assinatura antes de continuar');
      return;
    }

    setSigning(true);
    setError('');

    try {
      const response = await fetch(`/api/signatures/sign/${token}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          signature_data: signatureData,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to sign document');
      }

      setSuccess('Documento assinado com sucesso!');
      setTimeout(() => {
        navigate('/signature-complete');
      }, 2000);
    } catch (error) {
      setError(error.message);
    } finally {
      setSigning(false);
    }
  };

  const handleDecline = async () => {
    if (!declineReason.trim()) {
      setError('Por favor, informe o motivo da recusa');
      return;
    }

    setDeclining(true);
    setError('');

    try {
      const response = await fetch(`/api/signatures/decline/${token}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reason: declineReason,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to decline signature');
      }

      setSuccess('Assinatura recusada com sucesso.');
      setTimeout(() => {
        navigate('/signature-declined');
      }, 2000);
    } catch (error) {
      setError(error.message);
    } finally {
      setDeclining(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error && !documentData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <CardTitle className="text-red-700">Erro</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-center text-gray-600">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <CardTitle className="text-green-700">Sucesso</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-center text-gray-600">{success}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <FileText className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Assinatura Digital</h1>
          <p className="text-gray-600">Revise e assine o documento abaixo</p>
        </div>

        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-700">{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Document Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="w-5 h-5" />
                <span>Informações do Documento</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm font-medium text-gray-700">Título</Label>
                <p className="text-gray-900">{documentData?.signature?.document_title}</p>
              </div>
              
              {documentData?.signature?.document_description && (
                <div>
                  <Label className="text-sm font-medium text-gray-700">Descrição</Label>
                  <p className="text-gray-900">{documentData.signature.document_description}</p>
                </div>
              )}

              <div className="flex items-center space-x-4 pt-4 border-t">
                <div className="flex items-center space-x-2">
                  <User className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600">Signatário:</span>
                  <span className="text-sm font-medium">{documentData?.signature?.signer_name}</span>
                </div>
              </div>

              {documentData?.signature?.expires_at && (
                <div className="flex items-center space-x-2 text-sm text-orange-600">
                  <Clock className="w-4 h-4" />
                  <span>
                    Expira em: {new Date(documentData.signature.expires_at).toLocaleDateString('pt-BR')}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Signature Section */}
          <div className="space-y-6">
            {!showDeclineForm ? (
              <>
                <SignatureCanvas onSignatureChange={handleSignatureChange} />
                
                <div className="flex flex-col space-y-3">
                  <Button
                    onClick={handleSign}
                    disabled={!signatureData || signing}
                    className="w-full bg-green-600 hover:bg-green-700"
                  >
                    {signing ? 'Assinando...' : 'Assinar Documento'}
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={() => setShowDeclineForm(true)}
                    disabled={signing}
                    className="w-full border-red-300 text-red-600 hover:bg-red-50"
                  >
                    Recusar Assinatura
                  </Button>
                </div>
              </>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="text-red-700">Recusar Assinatura</CardTitle>
                  <CardDescription>
                    Por favor, informe o motivo da recusa
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="reason">Motivo da recusa</Label>
                    <Textarea
                      id="reason"
                      placeholder="Digite o motivo da recusa..."
                      value={declineReason}
                      onChange={(e) => setDeclineReason(e.target.value)}
                      rows={4}
                    />
                  </div>
                  
                  <div className="flex space-x-3">
                    <Button
                      onClick={handleDecline}
                      disabled={!declineReason.trim() || declining}
                      variant="destructive"
                      className="flex-1"
                    >
                      {declining ? 'Recusando...' : 'Confirmar Recusa'}
                    </Button>
                    
                    <Button
                      variant="outline"
                      onClick={() => setShowDeclineForm(false)}
                      disabled={declining}
                      className="flex-1"
                    >
                      Cancelar
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Legal Notice */}
        <Card className="mt-8">
          <CardContent className="pt-6">
            <div className="text-xs text-gray-500 space-y-2">
              <p>
                <strong>Aviso Legal:</strong> Ao assinar este documento digitalmente, você concorda que sua assinatura eletrônica 
                tem a mesma validade legal que uma assinatura manuscrita.
              </p>
              <p>
                Esta assinatura será registrada com carimbo de tempo e informações de auditoria para garantir 
                a integridade e autenticidade do documento.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SignDocument;

