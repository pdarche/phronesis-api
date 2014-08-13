$(document).ready(function(){
  var template

  $("#create input[type='submit']").on('click', function(ev){
    ev.preventDefault()
    var el        = $('#create')
      , stimulant = el.find('.stimulant').val()
      , amount    = el.find('.amount').val()
      , unit      = el.find('.unit').val()
      , data;

    data = {
      'stimulant' : stimulant,
      'amount'    : amount,
      'unit'      : unit,
    }

    console.log("posting")

    $.ajax({
      url: '/api/stimulants',
      type: 'POST',
      data: data,
      success: function(){
        alert('success')
      },
      error: function(){
        alert('error')
      }
    })  
  })


  // $('body').on('click', '.abstract h5, #controls h3', function(ev){
  //   var target = $(ev.target)

  //   if (!(target.next().hasClass('hidden'))){
  //     target.next().addClass('hidden')
  //   } else {
  //     target.next().removeClass('hidden')
  //   }
  // })
})

function renderTemplates(template, papers){
  var source   = $(template).html()
    , tmpl     = Handlebars.compile(source)
    , html     = tmpl({"papers":papers});

  $('#papers').html(html)
}
