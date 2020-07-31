window.initChat = (
  room, 
  player, 
  survivors,
  anonymous_price,
  voted_for_you_price,
  player_vote_price,
  see_messages_price,
  ) => {
  var state = {
    message_receiver: room,
    survivor_names: [],
    current_losers: [],
    isThirdPlace: false,
    isFinalRound: false,
    coins: 5,
    bounties: {},
    points: 0,
    round: 1,
    bankCoins: 0,
    anonymous_price : anonymous_price,
    voted_for_you_price: voted_for_you_price,
    player_vote_price: player_vote_price,
    see_messages_price: see_messages_price,
    hasVoted: false,
    objective: 'Pass',
    playerObjective: '',
    leaderboard: {},
    leaderboardCoins: {},
  }

//DOM Elements
const acceptTradeDOM = $('.accept-trade')
const coinCountDOM = $('.player-coin-count')
const tradeCoinInputDOM = $('.trade-input')
const tradePlayerInputDOM = $('.player-trade-input')
const setBountyPlayerInputDOM = $('.player-bounty-input')
const bountyInputDOM = $('.bounty-input')
const setBountyDOM = $('.bounty-set')
const bountiesDOM = $('.bounty-for-player')
const actionModalDOM =  $('#select-player-modal')
const gameOverDOM =  $('#game-over-modal')
const messageInputDOM = $('#chat-message-input')
const pointCointDOM = $('.point-count')
const roundDOM = $('.round')
const bankDOM = $('.bank-coin-count')
const yourButtonDOM = $('.your-button')
const playerObjectiveDOM = $('.player-objective')

$( document ).ready(function() {
  bountiesDOM.hide()
  const savedSession = localStorage.getItem('state') && JSON.parse(localStorage.getItem('state')) || state
  state = savedSession
  for (var key in survivors) {
    if(!state.survivor_names.includes(survivors[key].name)) {
      state.survivor_names.push(survivors[key].name)
    }
  }
  if (survivors.length < 4) {
    $('.vote-button').addClass('disabled')
  }

  state.survivor_names.forEach((s, index) => {
    renderVoteCount(s)
  })

  coinCountDOM.text(state.coins)
  renderBounties()
  renderPointCount()

  if(state.votee) {
    hasVotedRender()
  }
  validateCards()
  validateImmunity()
  hideModals()
  updateRound()
  renderLeaderboad()
  renderBank()
  renderObjective()
});

  $('.back').click(() => {
    location.href = "http://127.0.0.1:8000/";
  })
  //My wonderful websocket
  var chatSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/chat/'
    + room
    + '/'
  );

  chatSocket.onopen = function(e) {
    chatSocket.send(JSON.stringify({
      'player': player,
      'command': 'add_player'
    }))}

  chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
    setTimeout(function() {
    var chatSocket = new WebSocket(
      'ws://'
      + window.location.host
      + '/ws/chat/'
      + room
      + '/'
  );
    }, 1000);
  };


  function saveState() {
    localStorage.setItem('state', JSON.stringify(state));
  }

  //// RENDER FUNCTIONS ////
  function showModal(action) {
    state.intelAction = action
    actionModalDOM.show()
  }

  function hideModals() {
    actionModalDOM.hide()
    gameOverDOM.hide()
  }

  function renderBank() {
    bankDOM.text(state.bankCoins)
  }

  function tradeExecutedRender() {
    acceptTradeDOM.addClass('disabled')
    tradeCoinInputDOM.val('')
    tradePlayerInputDOM.val('')
    coinCountDOM .text(state.coins)
  }

  function renderBounties() {
    setBountyDOM.addClass('disabled')
    bountyInputDOM.val('')
    setBountyPlayerInputDOM .val('')
    coinCountDOM.text(state.coins)

    Object.keys(state.bounties).forEach(function(survivor) {
        const survivorDiv = $(`.survivor-wrapper[data-survivor=${survivor}]`)
        const bountyDiv = survivorDiv.find('.bounty-for-player')
        bountyDiv.show()
        bountyDiv.find('.bounty-amount').text(state.bounties[survivor])
    });

  }

  function hasVotedRender() {
    $('.vote-button').addClass('disabled');
    $(`.survivor-wrapper[data-survivor=${state.votee}]`).find('.survivor-pill').addClass('voted-out')
  }


  function renderVoteCount(s) {
    const survivorDiv = $(`.survivor-wrapper[data-survivor=${s}]`)
    var text = state[s] || 0
    var voteLabel = state[s] === 1 ? 'Vote' : 'Votes'
    var isLoser = state.current_losers.includes(s)
    $(survivorDiv).find('.vote-count').text(`${text} ${voteLabel}`)
    if(isLoser) {
      $(survivorDiv).find('.vote-count').addClass('loser')
    } else {
      $(survivorDiv).find('.vote-count').removeClass('loser')
    }
  }

  function renderNewPlayer(new_player) {
    var survivorDiv = $('.survivor-wrapper').clone()[0]
    $(survivorDiv).attr('data-survivor', new_player)
    $(survivorDiv).find('.vote-selection').text(`${new_player}`)
    $(survivorDiv).find('.vote-selection')
    $(survivorDiv).find('.vote-button').attr('data-survivor', new_player)
    $(survivorDiv).find('.vote-button').removeClass('your-button').text('Rob')
    $('.survivors-list').append(survivorDiv)
    state.survivor_names.push(new_player)
    if(state.survivor_names.length >= 4) {
      $('.vote-button').removeClass('disabled')
    }
    var leaderboardDiv = $('.score-row').clone()[0]
    $(leaderboardDiv).find('.leaderboard-point').attr('data-survivor', new_player)
    $(leaderboardDiv).find('.leaderboard-name').text(new_player)

    $(leaderboardDiv).find('.leaderboard-coins').attr('data-survivor', new_player)
    $('.leaderboard').append(leaderboardDiv)
  }

  function renderRedactedMessageState() {
    messageInputDOM.attr('placeholder', 'Send an anonymous message to the group or to a player...')
    messageInputDOM.addClass('redacted')
  }

  function renderPointCount() {
    pointCointDOM.text(state.points)
  }

  function renderLeaderboad() {
    for (var i in state.survivor_names) {
      const survivor = state.survivor_names[i]
      const points = state.leaderboard[`${survivor}`]
      const coins = state.leaderboardCoins[`${survivor}`]
      const rowDiv = $(`.point-count[data-survivor=${survivor}]`)
      const coinRowDiv = $(`.leaderboard-coins[data-survivor=${survivor}]`)
      rowDiv.text(points)
      coinRowDiv.text(coins)
    }
  }


  function renderObjective() {
    const label  = state.objective + ": " + state.playerObjective
    const objective = state.objective != 'Pass' ?  label : ' - - - - - - - - - - - - - - - - -'
    playerObjectiveDOM.text(objective)
  }
  ////  /////

  //// UTILITY FUNCTIONS ////
  function parseInput(message) {
    const regex = new RegExp('/w[ ][A-Za-z_]*')

    const splitReceiver = regex.exec(message) ? regex.exec(message)[0] : '' // /w example_mame
    const whispered = splitReceiver ? splitReceiver.split(' ')[1] : room // example_name
    // const newMessage = message.replace(splitReceiver + ' ', '')
    return whispered
  }

  function renderMessageSelectDropdown(message) {
    const regex = new RegExp(
      message.replace(/[-[\]{}()*+?.,\\/^$|#\s]/g, "\\$&"),
      "i"
    );
    var resultHTML = ''

    const result = state.survivor_names.filter(name => regex.test(name))
    const isLastOption = Object.keys(result).length == 1
    if(isLastOption) {
      $('.tab-select').show()
    } 
    else {
      $('.tab-select').hide()
    }
    for (var key in result) {
      const survivor = result[key]
      const selected = isLastOption ? 'selected' : ''
      if(survivor != player) {
        resultHTML += `<div class='message-survivor-option ${selected}' data-survivor=${survivor}>${survivor}</div>`
      }
    }
    $('.survivor-name-dropdown').html(resultHTML)
  }


  function formatMessage(privateMessage, isOwnPrivateMessage , roomMessage, data) {
    if(privateMessage) {
      return '[' + data.player + ' whispers]: ' 
    }
    if(isOwnPrivateMessage && !roomMessage) {
      return '[' + `you whispered ${data.receiver}` +  ']: ' 
    }
    return '[' + data.player + ']: '
  }

  function validateTrade() {
    const hasValidTrade = Number(tradeCoinInputDOM.val()) <= state.coins && tradeCoinInputDOM.val() != 0
    const isValidPlayer = state.survivor_names.includes(tradePlayerInputDOM.val()) && tradePlayerInputDOM.val() != player
    if(hasValidTrade && isValidPlayer && state.survivor_names.length >= 4) {
      acceptTradeDOM.removeClass('disabled')
    } else {
      acceptTradeDOM.addClass('disabled')
    }
  }

  function validateCards() {
    const all_cards = $('.intel-card')
    all_cards.each((i) => {
      const card = $(all_cards[i]).find('.wrapper')
      const price = state[card.attr('data-card-price')]
      if(price > state.coins || state.survivor_names.length < 4) {
        card.addClass('disabled')
      } else {
        card.removeClass('disabled')
      }
    })
  }


  function validateBounty() {
    const hasValidBounty = Number(bountyInputDOM.val()) <= state.coins && bountyInputDOM.val() != 0
    const isValidPlayer = state.survivor_names.includes(setBountyPlayerInputDOM.val())
    if(hasValidBounty&& isValidPlayer && state.survivor_names.length >= 4) {
      setBountyDOM.removeClass('disabled')
    } else {
      setBountyDOM.addClass('disabled')
    }
  }

  function validateImmunity() {
    if(state.coins < 5 || state.survivor_names.length < 4 || state.hasVoted) {
      yourButtonDOM.addClass('disabled')
    } else {
      yourButtonDOM.removeClass('disabled')
    }

  }
  ////  ////


  function updateRound() {
    roundDOM.text(state.round)
  }

  chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    //Incoming Message
    var roomMessage = data.receiver === room
    var privateMessage = data.receiver === player
    var isOwnPrivateMessage = data.player === player
    if (roomMessage || privateMessage || isOwnPrivateMessage && data.message){
        var label = formatMessage(privateMessage, isOwnPrivateMessage, roomMessage, data)
        document.querySelector('#chat-log').value += ( label + data.message + '\n');
        $('#chat-log').scrollTop($('#chat-log')[0].scrollHeight);
    }

    if (data.message_card) {
      for (var i in data.messages) {
        const message = data.messages[i]
        if(message.receiver != room) {
          document.querySelector('#chat-log').value += ( '[' + message.sender + ' TO ' + message.receiver + ']: ' + message.message + '\n');
        }
      }
    }

    if (data.see_votes_from_player) {
      for (var i in data.all_votes) {
        const vote = data.all_votes[i]
        document.querySelector('#chat-log').value += ( '[VOTE INTEL]: ' + vote + '\n');
      }
    }

    if (data.see_votes) {
      for (var i in data.all_votes) {
        const vote = data.all_votes[i]
        document.querySelector('#chat-log').value += '[VOTED FOR YOU]: ' + vote + '\n'
      }
    }

    //kick loser(s) if round over
    if(data.round_over === true) {
      state.current_losers = data.current_losers
      state.hasVoted = false
      state.coins = data.coins
      state.round = data.round
      state.votee = null
      state.points = data.points
      state.leaderboard = data.leaderboard
      state.leaderboardCoins = data.leaderboard_coins
      state.objective = data.objective
      state.playerObjective = data.player_objective
      state.bounties = {}

      updateRound()
      coinCountDOM.text(state.coins)
      $('.bounty-for-player').hide()
      renderPointCount()
      saveState()
      if(state.current_losers.includes(player)) {
        console.log('loser')
      }
      $('.vote-button').removeClass('disabled')
      $('.survivor-pill').removeClass('voted-out')
      state.survivor_names.forEach((s, index) => {
        state[s] = data[s]
        renderVoteCount(s)
        saveState()
      })
    }

    // //Generate final round state.
    // if(data.final_round === true) {
    //   state.votee = null
    //   state.current_losers = data.current_losers
    //   if(data.current_losers.includes(player)) {
    //     state.isThirdPlace = true
    //     youAreThirdPlaceRender()
    //   } else {
    //     state.isFinalRound = true
    //     youAreInFinalRoundRender(data)
    //   }
    //   $('.survivor-pill').removeClass('voted-out')
    //   saveState()
    // }

    if(data.game_over === true) {
      gameOverDOM.show()
      gameOverDOM.find('.winner-text').text(data.winner + ' has won!')
      saveState()
    }

    if(data.bank_coins != undefined) {
      state.bankCoins = data.bank_coins
      saveState()
      renderBank() 
    }

    //Player has joined, create new element
    if(data.is_new_player && data.player != player && !state.survivor_names.includes(data.player)) {
      renderNewPlayer(data.player)
    }

    if(data.trade) {
      state.coins = data.coins
      tradeExecutedRender()
      saveState()
    }

    if(data.new_bounty) {
      state.bounties[data.set_for] = data.new_bounty
      saveState()
      renderBounties()
    }
    if(data.coins != undefined) {
      state.coins = data.coins
      coinCountDOM.text(data.coins)
      saveState()
    }
    validateCards()
    validateImmunity()
    renderLeaderboad()
    renderObjective()

  };



  $('#chat-message-input').bind('keydown', e => {
   const messageInputDom = document.querySelector('#chat-message-input');
   if (e.which === 9) { //tab
      e.preventDefault();
      if($('.message-survivor-option.selected').length) {
        messageInputDom.value = "/w " + $('.message-survivor-option.selected').attr('data-survivor')
        $(messageInputDom).trigger("change");
      }
    }
  })



  $('#chat-message-input').bind("keyup", e => {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    const whispered = parseInput(message)
    if(message.includes('/w ')) {
      const rawMessage = message.replace('/w ', '')
      renderMessageSelectDropdown(rawMessage)
      $('.dropdown-wrapper').show()
    } else {
      $('.dropdown-wrapper').hide()
    }
    if(state.survivor_names.includes(whispered) && whispered != player) {
      $('.dropdown-wrapper').hide()
      state.message_receiver = whispered
      $('#chat-message-input').addClass('private-message')
      messageInputDom.value = ''
      messageInputDom.placeholder = `Whisper ${state.message_receiver}...`
    }
    if (e.which === 13) {  // enter, return 

      if(message != '') { 
        if (state.is_redacted && state.message_receiver != room) { //Quick fix to show your own anonymous message (REFACTOR)
          document.querySelector('#chat-log').value += '[Anonymous whisper to ' + state.message_receiver + ']: ' + message + '\n'
        }

        chatSocket.send(JSON.stringify({
            'message': message,
            'command': 'chat_message',
            'player': player,
            'receiver' : state.message_receiver,
            'is_redacted': state.is_redacted
        }));
        state.is_redacted = false
    }
      messageInputDom.value = '';
      messageInputDOM.removeClass('redacted')
      messageInputDom.placeholder = 'Chat to Form Alliances... /w to private message'
      state.message_receiver = room
      $('#chat-message-input').removeClass('private-message')
    }
  });

  $('.vote-button').live('click', e => {
    state.votee = e.currentTarget.getAttribute('data-survivor')
    state.hasVoted = true;
    hasVotedRender()
    chatSocket.send(JSON.stringify({
        'player': player,
        'votee' : state.votee ,
        'command': 'vote',
    }))
    saveState()
    });

  tradePlayerInputDOM.bind('keyup', e => {
    validateTrade()
  })

  tradeCoinInputDOM.bind('keyup', e => {
    validateTrade()
  })


  setBountyPlayerInputDOM.bind('keyup', e => {
    validateBounty()
  })

  setBountyDOM.bind('keyup', e => {
    validateBounty()
  })

  $('.survivor-name-dropdown').click(e => {
    const survivor = $(e.target).attr('data-survivor')
    $('#chat-message-input').val(`/w ${survivor}`)
    $('#chat-message-input').keyup()
  })

  $('.accept-trade').click(e => {
    const playerToTrade = $('.player-trade-input').val()
    const trade = Number($('.trade-input').val())
    chatSocket.send(JSON.stringify({
      'trader' : player,
      'tradee' : playerToTrade,
      'coins': trade,
      'command': 'trade'
    }))
  })

  $('.bounty-set').click(e => {
    const setFor = setBountyPlayerInputDOM.val()
    const bountyAmount = Number(bountyInputDOM.val())
    chatSocket.send(JSON.stringify({
      'setter' : player,
      'set_for' : setFor,
      'bounty_amount': bountyAmount,
      'command': 'bounty'
    }))
  })


  //// Intel Card Clicks ////
  $('.message-card').click(e=> {
    showModal('message_card')
  })

  $('.vote-card').click(e=> {
    chatSocket.send(JSON.stringify({
      'player': player,
      'command': 'see_votes'
    }))
  })

  $('.anonymous-card').click(e=> {
    state.is_redacted = true 
    renderRedactedMessageState()
    })

  $('.vote-from-player-card').click(e=> {
    showModal('see_votes_from_player')
  })
  //// ////

  $('.close-modal').click(e => {
    e.preventDefault()
    hideModals()
  })

  $('.accept-action-item').click(e => {
    const targetPlayer = $('.action-item-input').val()
    actionModalDOM.hide()
    chatSocket.send(JSON.stringify({
      'player': player,
      'target_player': targetPlayer,
      'command': state.intelAction
    }))

  })

}

