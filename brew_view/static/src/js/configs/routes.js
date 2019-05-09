
routeConfig.$inject = ['$stateProvider', '$urlRouterProvider', '$locationProvider'];

/**
 * routeConfig - routing config for the application.
 * @param  {type} $stateProvider     Angular's $stateProvider object.
 * @param  {type} $urlRouterProvider Angular's $urlRouterProvider object.
 * @param  {type} $locationProvider  Angular's $locationProvider object.
 */
export default function routeConfig($stateProvider, $urlRouterProvider, $locationProvider) {
  const basePath = 'partials/';

  $urlRouterProvider.otherwise('/default/');

  // // use the HTML5 History API
  // $locationProvider.html5Mode(true);

  $stateProvider
    .state('namespace', {
      url: '/:namespace',
      params: {
        namespace: {
          value: 'default',
        },
      },
    })
    .state('namespace.landing', {
      url: '/',
      templateUrl: basePath + 'landing.html',
      controller: 'LandingController',
    })
    .state('login', {
      url: '/login',
      templateUrl: basePath + 'login.html',
      controller: 'LoginController',
    })
    // Unused by our UI, but helpful for external links.
    .state('namespace.systemID', {
      url: '/systems/:id',
      templateUrl: basePath + 'system_view.html',
      controller: 'SystemViewController',
    })
    .state('namespace.system', {
      'url': '/systems/:name/:version',
      'templateUrl': basePath + 'system_view.html',
      'controller': 'SystemViewController',
    })
    .state('about', {
      url: '/:namespace/about',
      templateUrl: basePath + 'about.html',
      controller: 'AboutController',
    })
    .state('jobs', {
      url: '/:namespace/jobs',
      templateUrl: basePath + 'job_index.html',
      controller: 'JobIndexController',
    })
    .state('jobsCreate', {
      url: '/:namespace/jobs/create',
      templateUrl: basePath + 'job_create.html',
      controller: 'JobCreateController',
      params: {
        'request': null,
        'system': null,
        'command': null,
      },
    })
    .state('job', {
      'url': '/:namespace/jobs/:id',
      'templateUrl': basePath + 'job_view.html',
      'controller': 'JobViewController',
    })
    .state('commands', {
      url: '/:namespace/commands',
      templateUrl: basePath + 'command_index.html',
      controller: 'CommandIndexController',
    })
    .state('command', {
      url: '/:namespace/systems/:systemName/:systemVersion/commands/:name',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
        id: null,
      },
    })
    // Unused by our UI, but helpful for external links.
    .state('commandID', {
      url: '/:namespace/commands/:id',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
      },
    })
    .state('namespace.requests', {
      url: '/requests',
      templateUrl: basePath + 'request_index.html',
      controller: 'RequestIndexController',
    })
    .state('namespace.request', {
      url: '/requests/:request_id',
      templateUrl: basePath + 'request_view.html',
      controller: 'RequestViewController',
    })
    .state('queues', {
      url: '/:namespace/admin/queues',
      templateUrl: basePath + 'admin_queue.html',
      controller: 'AdminQueueController',
    })
    .state('system_admin', {
      url: '/:namespace/admin/systems',
      templateUrl: basePath + 'admin_system.html',
      controller: 'AdminSystemController',
    })
    .state('user_admin', {
      url: '/admin/users',
      templateUrl: basePath + 'admin_user.html',
      controller: 'AdminUserController',
    })
    .state('role_admin', {
      url: '/admin/roles',
      templateUrl: basePath + 'admin_role.html',
      controller: 'AdminRoleController',
    });
};
