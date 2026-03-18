<!--
  Widget Assistance IA Télécom
  
  Copiez ce code dans n'importe quel site web pour ajouter
  un bouton flottant qui ouvre le chatbot.
  
  Changez CHATBOT_URL par l'adresse de votre serveur Flask.
-->

<script>
(function(){
    var CHATBOT_URL = "http://localhost:5000"; // ← Changez cette URL
    
    // Styles
    var style = document.createElement('style');
    style.textContent = `
        #iat-widget-btn {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #5b4cdb, #8b7ff5);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(91,76,219,0.4);
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        #iat-widget-btn:hover {
            transform: scale(1.08);
            box-shadow: 0 6px 28px rgba(91,76,219,0.5);
        }
        #iat-widget-btn svg {
            width: 28px;
            height: 28px;
        }
        #iat-widget-btn.open svg.ic-chat { display: none; }
        #iat-widget-btn.open svg.ic-close { display: block; }
        #iat-widget-btn:not(.open) svg.ic-chat { display: block; }
        #iat-widget-btn:not(.open) svg.ic-close { display: none; }
        
        #iat-widget-frame {
            position: fixed;
            bottom: 96px;
            right: 24px;
            width: 380px;
            height: 580px;
            border: none;
            border-radius: 20px;
            box-shadow: 0 12px 40px rgba(27,19,64,0.2);
            z-index: 99998;
            opacity: 0;
            transform: translateY(20px) scale(0.95);
            pointer-events: none;
            transition: all 0.3s ease;
        }
        #iat-widget-frame.open {
            opacity: 1;
            transform: translateY(0) scale(1);
            pointer-events: auto;
        }
        
        @media (max-width: 480px) {
            #iat-widget-btn {
                bottom: 16px;
                right: 16px;
                width: 52px;
                height: 52px;
            }
            #iat-widget-frame {
                bottom: 0;
                right: 0;
                width: 100%;
                height: 100%;
                border-radius: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Button
    var btn = document.createElement('button');
    btn.id = 'iat-widget-btn';
    btn.title = 'Assistance IA Télécom';
    btn.innerHTML = `
        <svg class="ic-chat" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <svg class="ic-close" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
    `;
    
    // Iframe
    var frame = document.createElement('iframe');
    frame.id = 'iat-widget-frame';
    frame.src = '';
    
    // Toggle
    btn.addEventListener('click', function(){
        var isOpen = btn.classList.toggle('open');
        frame.classList.toggle('open');
        if (isOpen && !frame.src) {
            frame.src = CHATBOT_URL + '/chat';
        }
    });
    
    document.body.appendChild(frame);
    document.body.appendChild(btn);
})();
</script>
