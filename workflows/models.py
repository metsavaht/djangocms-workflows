# -*- coding: utf-8 -*-

from cms.extensions.models import TitleExtension
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from treebeard.mp_tree import MP_Node


class Workflow(models.Model):
    name = models.CharField(
        _('Name'),
        max_length=63,
        unique=True,
        help_text=_('Please provide a descriptive name!')
    )

    default = models.BooleanField(
        _('Default workflow'),
        default=False,
        help_text=_('Should this be the default workflow for all pages?')
    )

    class Meta:
        verbose_name = _('Workflow')
        verbose_name_plural = _('Workflows')

    def save(self, **kwargs):
        if self.default:
            Workflow.objects.filter(default=True).exclude(pk=self.pk).update(default=False)
        super(Workflow, self).save(**kwargs)

    @classmethod
    def default_workflow(cls):
        return cls.objects.get(default=True)

    @cached_property
    def mandatory_stages(self):
        return self.stages.filter(optional=False)


class WorkflowStage(models.Model):
    workflow = models.ForeignKey(
        'workflows.Workflow',
        on_delete=models.CASCADE,
        verbose_name=_('Workflow'),
        related_name='stages'
    )

    group = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
        verbose_name=_('Group'),
        help_text=_('Only members of this group can approve this workflow stage.'),
    )

    # admin-sortable required
    order = models.PositiveSmallIntegerField(
        _('Order'),
        default=0
    )

    optional = models.BooleanField(
        _('Optional'),
        default=False,
        help_text=_('Is this workflow stage optional?')
    )

    class Meta:
        verbose_name = _('Workflow stage')
        verbose_name_plural = _('Workflow stages')
        ordering = ('order',)
        unique_together = (('workflow', 'group'),)

    @cached_property
    def next_mandatory_stage(self):
        return self.workflow.stages.filter(order__gt=self.order, optional=False).first()

    @cached_property
    def possible_successors(self):
        nms = self.next_mandatory_stage
        pending = self.workflow.stages.filter(order__gt=self.order)
        if nms is not None:
            pending = pending.filter(order__lte=nms.order)
        return pending


class WorkflowExtension(TitleExtension):
    workflow = models.ForeignKey(
        'workflows.Workflow',
        on_delete=models.CASCADE,
        verbose_name=_('Workflow'),
        help_text=_('The workflow set here is language specific.')
    )

    descendants = models.BooleanField(
        _('Descendants'),
        help_text=_('Should this workflow apply to descendant pages?'),
        default=True
    )

    class Meta:
        verbose_name = _('Workflow extension')
        verbose_name_plural = _('Workflow extensions')

    def open(self, user):
        """

        :param user:
                User submitting changes.
        :rtype: Action
        :return: Initial open-Action of a workflow
        """
        # TODO
        return None


class Action(MP_Node):
    """

    """
    REQUEST, APPROVE, REJECT, CANCEL, FINISH = 'request', 'approve', 'reject', 'cancel', 'finish'

    TYPES = (
        (REQUEST, _('request')),
        (APPROVE, _('approve')),
        (REJECT, _('reject')),
        (CANCEL, _('cancel')),
        (FINISH, _('finish')),
    )

    title = models.ForeignKey(
        'cms.Title',
        on_delete=models.CASCADE,
        verbose_name=_('Title'),
    )

    # persist workflow in case the workflow changes on the title
    workflow = models.ForeignKey(
        'workflows.Workflow',
        on_delete=models.CASCADE,
        verbose_name=_('Workflow'),
    )

    stage = models.ForeignKey(
        'workflows.WorkflowStage',
        on_delete=models.SET_NULL,
        verbose_name=_('Stage'),
        # allow null for open action and if Stage is deleted on Workflow
        null=True,
        default=None,
    )

    # persist stage Group in case stage is deleted
    group = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
        verbose_name=_('Group'),
        null=True,
        default=None
    )

    action_type = models.CharField(
        _('Action type'),
        max_length=10,
        choices=TYPES,
        default=REQUEST,
    )

    created = models.DateTimeField(
        _('Created'),
        auto_now_add=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        verbose_name=_('User'),
        null=True
    )

    message = models.TextField(
        _('Message'),
        help_text=_('Provide more information!')
    )

    class Meta:
        verbose_name = _('Workflow action')
        verbose_name_plural = _('Workflow actions')
        unique_together = (('title', 'stage'),)
        ordering = ('depth', 'created')

    def get_request(self):
        """Root of this chain of actions.

        :rtype: Action
        :return:
        """
        return self.get_root()

    def get_author(self):
        """Return author of changes.

        :rtype: get_user_model()
        :return: author of changes
        """
        return self.get_request().user

    def approve(self, stage, user):
        """

        :param stage:
                Stage to be approved. Must be valid successor Stage to this Stage.
        :param user:
                User approving stage. Must be a member of Stage's group.
        :type stage: WorkflowStage
        :rtype: Action
        :return: Approve-Action of stage
        """
        # this stage must be of type OPEN or APPROVED
        # TODO
        return None

    def reject(self, stage, user):
        """

        :param stage:
                Stage to be rejected. Must be valid successor Stage to this Stage.
        :param user:
                User rejecting stage. Must be a member of Stage's group.
        :type stage: WorkflowStage
        :rtype: Action
        :return: Reject-Action of stage
        """
        # this stage must be of type OPEN or APPROVED
        # TODO
        return None

    def cancel(self, user):
        """

        :param user:
                User canceling entire workflow.
        :rtype: Action
        :return: Cancel-Action
        """
        # TODO
        return None