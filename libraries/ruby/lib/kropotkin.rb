#!/usr/bin/ruby
require 'kropotkin/version'
require 'json'
require 'net/http'
require 'open3'
require 'uri'

module Kropotkin
  class << self
    LOCAL_SUBSCRIPTIONS = {}

    def make_query_function(confidence, which, number)
      return lambda {|factspace, type, criteria| \
        get_statements(confidence, which, number,
                       factspace, type, criteria)}
    end

    def get_newest_fact(factspace, type, criteria)
      f = make_query_function('fact', 'newest', 1)
      f.call(factspace, type, criteria)
    end

    def get_all_facts(factspace, type, criteria)
      f = make_query_function('fact', 'all', nil)
      f.call(factspace, type, criteria)
    end

    def store_fact(factspace, type, content)
      store_statement('fact', factspace, type, content)
    end

    def store_opinion(factspace, type, content)
      store_statement('opinion', factspace, type, content)
    end

    def create_factspace(name, timeout=5)
      if !store_fact('kropotkin', 'factspace_wanted', {'name' => name})
        return false
      end
      finish = Time.now.to_i + timeout
      while Time.now.to_i < finish
        if get_newest_fact('kropotkin', 'factspace', {'name' => name})
          return true
        end
      end
      return false
    end

    def subscribe(factspace, confidence, type)
      identifier = execute_queue_command('create_queue')
      if !identifier
        return false
      end

      content = {'type' => type, 'confidence' => confidence,
                 'queue' => identifier}
      if !store_fact(factspace, 'subscription', content)
        return false
      end

      LOCAL_SUBSCRIPTIONS[[factspace, confidence, type]] = identifier
      return true
    end

    def get_next_statement(factspace, confidence, type)
      return internal_get_next_statement(factspace, confidence, type, true)
    end

    def get_next_statement_noblock(factspace, confidence, type)
      return internal_get_next_statement(factspace, confidence, type, false)
    end

    def internal_get_next_statement(factspace, confidence, type, block)
      if block == true
        dequeue_command = 'dequeue'
      else
        dequeue_command = 'dequeue_noblock'
      end

      identifier = LOCAL_SUBSCRIPTIONS[[factspace, confidence, type]]
      loop do
        result = execute_queue_command(dequeue_command, nil, identifier)
        if result
          return JSON.parse(result)
        elsif block == false
          return false
        end
      end
    end

    def execute_queue_command(command, input=nil, identifier=nil)
      queue = ENV['KROPOTKIN_QUEUE']
      if identifier
        result = Open3.capture3(queue, command, identifier, :stdin_data=>input)
      else
        result = Open3.capture3(queue, command, :stdin_data=>input)
      end
      output, error, status = result
      if status.exitstatus != 0
        return false
      else
        return output
      end
    end

    def get_my_computer_name()
      kropotkin_url = ENV['KROPOTKIN_URL']
      url = '%s/mycomputername' % kropotkin_url
      uri = URI.parse(url)
      http = Net::HTTP.new(uri.host, uri.port)
      resp = http.post(url, JSON.dump(content))
      if resp.code != '200'
        return false
      else
        return resp.body
      end
    end

    def store_statement(confidence, factspace, type, content)
      if type != 'constitution_element'
        query_content = {'type' => type, 'confidence' => confidence}
        subscriptions = get_all_facts(factspace, 'subscription', query_content)
        if subscriptions and subscriptions.length > 0
          for subscription in subscriptions
            identifier = subscription['queue']
            execute_queue_command('enqueue', JSON.dump(content), identifier)
          end
        end
      end

      kropotkin_url = ENV['KROPOTKIN_URL']
      url = '%s/factspace/%s/%s/%s' \
                 % [kropotkin_url, factspace, confidence, type]
      uri = URI.parse(url)
      http = Net::HTTP.new(uri.host, uri.port)
      resp = http.post(url, JSON.dump(content))
      if resp.code != '200'
        return false
      else
        return resp.body.to_i
      end
    end

    def get_statements(confidence, which, number, factspace, type, criteria)
      kropotkin_criteria_list = []
      if which != 'all'
        kropotkin_criteria_list.push('result-' + which)
      end
      if number
        kropotkin_criteria_list.push('number-' + number.to_s)
      end

      criteria = Hash[criteria]
      if kropotkin_criteria_list.length > 0
        criteria['kropotkin_criteria'] = kropotkin_criteria_list.join(',')
      end
      statements = get_all_statements(confidence, factspace, type, criteria)
      if statements.length > 0 and (number.nil? or number > 1)
        return statements
      elsif statements.length > 0 and number == 1
        return statements[0]
      else
        return nil
      end
    end

    def get_all_statements(confidence, factspace, type, criteria)
      kropotkin_url = ENV['KROPOTKIN_URL']
      params = URI.encode_www_form(criteria)
      url = '%s/factspace/%s/%s/%s?%s' %
                [kropotkin_url, factspace, confidence, type, params]
      uri = URI.parse(url)
      http = Net::HTTP.new(uri.host, uri.port)
      resp = http.get(url)
      if resp.code == '200'
        return JSON.parse(resp.body)
      else
        raise 'Unexpected response from server: %s' % resp.code
      end
    end
  end
end
