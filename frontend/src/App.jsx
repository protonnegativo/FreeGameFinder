import { useEffect, useState } from 'react'

function App() {
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [email, setEmail] = useState('')
  const [subMessage, setSubMessage] = useState('')

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${API_URL}/api/v1/games`)
      .then(res => res.json())
      .then(data => {
        setGames(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Erro ao buscar jogos:", err)
        setLoading(false)
      })
  }, [])

  const handleSubscribe = async (e) => {
    e.preventDefault()
    if (!email) return
    
    setSubMessage("Processando...")
    try {
      const res = await fetch(`${API_URL}/api/v1/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      })
      const data = await res.json()
      setSubMessage(data.message)
      if (res.ok) setEmail('') // Limpa o campo se der sucesso
    } catch (err) {
      setSubMessage("Erro ao tentar se inscrever. Tente novamente.")
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center p-8 font-sans">
      <header className="mb-12 text-center mt-8 w-full max-w-lg">
        <h1 className="text-5xl font-bold text-primary mb-4 tracking-tight">FreeGameFinder</h1>
        <p className="text-xl opacity-80 mb-8">Nunca mais perca um jogo grátis.</p>
        
        <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-2 w-full">
          <input 
            type="email" 
            placeholder="Cadastre seu e-mail..." 
            className="flex-grow p-3 rounded bg-surface border border-gray-700 text-textPrimary focus:outline-none focus:border-primary"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button type="submit" className="bg-primary text-background font-bold py-3 px-6 rounded hover:bg-primary/80 transition-colors whitespace-nowrap">
            Ativar Alertas
          </button>
        </form>
        {subMessage && <p className="mt-4 text-sm text-primary font-semibold">{subMessage}</p>}
      </header>
      
      <main className="w-full max-w-5xl">
        {loading ? (
          <div className="text-center text-textPrimary animate-pulse">Buscando ofertas...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {games.map(game => (
              <div key={game.id} className="bg-surface rounded-xl shadow-2xl border border-gray-800 overflow-hidden flex flex-col hover:border-primary/50 transition-colors">
                <img 
                  src={game.cover_image_url} 
                  alt={game.title} 
                  className="w-full h-48 object-cover border-b border-gray-800"
                />
                <div className="p-6 flex flex-col flex-grow">
                  <div className="flex justify-between items-start mb-2">
                    <h2 className="text-xl font-bold text-textPrimary line-clamp-2">{game.title}</h2>
                  </div>
                  
                  <div className="flex flex-wrap gap-2 mb-4">
                    <div className="text-sm font-semibold text-gray-400 bg-gray-800/50 px-2 py-1 rounded">
                      {game.platform}
                    </div>
                    {game.email_sent ? (
                      <div className="text-sm font-semibold text-primary bg-primary/10 px-2 py-1 rounded border border-primary/20">
                        ✅ E-mail Enviado
                      </div>
                    ) : (
                      <div className="text-sm font-semibold text-gray-500 bg-gray-800/30 px-2 py-1 rounded border border-gray-700/30">
                        ⏳ Não Enviado
                      </div>
                    )}
                  </div>
                  
                  <div className="mt-auto pt-4 flex items-center justify-between border-t border-gray-800/50">
                    <div className="flex flex-col">
                      {game.original_price && <span className="text-xs line-through text-gray-500">R$ {game.original_price}</span>}
                      <span className="text-primary font-bold">Grátis</span>
                    </div>
                    <a href={game.claim_url} target="_blank" rel="noopener noreferrer" className="bg-primary text-background font-bold py-2 px-4 rounded hover:bg-primary/80 transition-colors">
                      Resgatar
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

export default App