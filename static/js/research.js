$(document).ready(function(){
  $('#search').keyup(function(){
    var el = $(this)
      , title = el.find('.title').val()
      , keywords = el.find('.keywords').val()
      , favorite = el.find('.favorite').is(":checked")
      , data;

    data = {
      'title':title,
      'keyword': keywords
    }

    $.getJSON('/api/research', data, function(data){
      console.log('data', data)
    })

  })

  $("#create input[type='submit']").on('click', function(ev){
    ev.preventDefault()
    var el = $('#create')
      , title = el.find('.title').val()
      , url = el.find('.url').val()
      , keywords = el.find('.keywords').val()
      , note = el.find('.note').val()
      , abstract = el.find('.abstract').val()
      , favorite = el.find('.favorite').is(":checked")
      , data;

    data = {
      'title'   : title,
      'url'     : url,
      'keywords': keywords,
      'note'    : note,
      'abstract': abstract,
      'favorite': favorite
    }

    $.ajax({
      url: '/api/research',
      type: 'POST',
      data: data,
      success: function(){
        alert('success')
        el.find('input').empty()
      },
      error: function(){
        alert('error')
      }
    })  
  })
})